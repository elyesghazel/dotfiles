# gopro sharing — VPS side

Server-side runbook for the two "get a clip out" front-ends that sit next to
Jellyfin: **gopro-share** (private download links) and the **Cloudreve mirror**
(phone browsing). The desktop scripts are in `README.md`; this is what lives on the
VPS (`ssh server`, Docker + Traefik, network `traefik_proxy`, entrypoint `https`,
certresolver `cloudflare`).

Everything below reads the same stream copies Jellyfin serves, at `/srv/media/gopro`.

---

## 1. gopro-share — private links + dashboard

`share.elyesghazel.ch/<token>/` → a generated dashboard listing every clip in that
share: poster thumbnails, in-browser playback, and a per-clip quality picker
(stream copy vs. 4K original). No account. `gopro share` (desktop) resolves the clip
names, then hands the work to the server.

**DNS:** `share.elyesghazel.ch` A → `159.195.34.0`, **grey-cloud / unproxied** (like
`media.`). Direct-to-VPS is required — Cloudflare's proxy caps downloads/uploads.
(Created via Traefik's `CF_DNS_API_TOKEN` in `/opt/docker/traefik/.env`.)

**Container:** `apps-gopro-share` — plain nginx serving the share dir read-only.
Compose + config at `/opt/docker/gopro-share/`:

- `docker-compose.yml` — `nginx:alpine`, mounts `/srv/media/gopro-share:…:ro` and
  `./nginx.conf`, Traefik router `Host(share.elyesghazel.ch)` → port 80.
- `nginx.conf` — `autoindex off` + `location = / { return 404; }` (tokens are the
  only way in); `location ~ /\.` denies the bookkeeping files; range requests work.

**The two-path trick:** a token dir is served twice.

| Path | Header | Used for |
|------|--------|----------|
| `/<token>/v/<clip>.mp4` | none | the dashboard's `<video>` — plays and seeks inline |
| `/<token>/dl/v/<clip>.mp4` | `Content-Disposition: attachment` | the download buttons |

`/dl/` is an `alias` in a named-capture regex location, so the *same file* is
reachable both ways. This matters: `Content-Disposition: attachment` on the media
itself is what stops in-browser playback, which is why the old single-path config
couldn't have a dashboard.

**Builder:** `/opt/docker/gopro-share/gopro-share-build` + `gopro-share-page.py`
(kept in the dotfiles repo under `gopro/server/`, **rsync'd on every `gopro share`
run** so the deployed copy can't drift). It hard-links the stream copies into
`<token>/v/`, makes poster frames in `<token>/t/` with ffmpeg, stages the 4K
originals into `<token>/4k/` from `mycloud:` directly (never route those through the
desktop), writes `.meta.json`, and renders `index.html`. Needs `python3`, `ffmpeg`
and `rclone` on the host.

Two things it deliberately does **once per share, not once per clip**: the archive
listing (`rclone lsf -R` is a full network round trip) and the staging transfer.
`--transfers` only parallelises across *files*, so one `rclone copy --files-from`
for the whole share runs at ~83 MB/s where a loop of single-file calls manages ~20.
rclone preserves the archive's subdirs, so the batch is flattened to the sanitized
names the page links to afterwards.

Staged originals are real copies and cost disk until expiry, so the builder tracks
planned bytes against `df` and skips any original that would leave less than
`DISK_MARGIN_GB` (default 20) free — that clip just keeps the single stream rung in
its picker.

Token dir layout:

```
/srv/media/gopro-share/<token>/
├── index.html        generated dashboard
├── .expires          epoch stamp, read by expire.sh   (403 via nginx)
├── .meta.json        what the page was rendered from  (403 via nginx)
├── v/<clip>.mp4      stream copy, hard-linked → costs no disk
├── t/<clip>.jpg      poster frame
└── 4k/<clip>.MP4     the original; a real copy, so it does cost disk
```

```bash
cd /opt/docker/gopro-share && docker compose up -d      # (re)deploy
# NOTE: rsyncing nginx.conf replaces the inode and breaks the bind mount --
# `docker compose up -d --force-recreate` after editing it, not `nginx -s reload`.
```

**Expiry:** each token dir holds a `.expires` file (epoch). `expire.sh` deletes dirs
past their stamp, run hourly by cron:

```
17 * * * * /opt/docker/gopro-share/expire.sh
```

---

## 2. Cloudreve mirror — browse/grab clips on the phone

With `CLOUDREVE_SYNC=1` in `gopro.conf`, `gopro-import` SSHes in after upload and runs
`/opt/docker/gopro-share/cloudreve-mirror.sh`, which mirrors `/srv/media/gopro` into
Cloudreve under `GoPro/`. They then show up in the Cloudreve app at
`files.elyesghazel.ch` (dated folders).

**Two things that make this non-obvious:**

1. **Cloudreve only shows files uploaded *through* Cloudreve** — a WebDAV/API write
   creates the DB row that makes a file appear. Dropping files straight into its
   storage dir (`/mnt/mycloud`, = rclone mount `mycloud:cloudreve`) does nothing.
   So the mirror uploads over **WebDAV**, not by copying into the storage dir.

2. **Cloudflare's 100 MB upload cap.** `files.elyesghazel.ch` is Cloudflare-proxied
   and rejects bodies >100 MB (HTTP 413); many stream copies are bigger. So the mirror
   talks to the **Cloudreve container directly on the docker network**
   (`http://<container-ip>:5212/dav`) — no Cloudflare, no Traefik, no cap. The
   container IP is resolved fresh each run (`docker inspect apps-cloudreve-backend`),
   so it survives container recreates; the script maintains a `CloudReveDirect`
   rclone remote in the server's `~/.config/rclone/rclone.conf` pointed at it.

```bash
/opt/docker/gopro-share/cloudreve-mirror.sh     # manual full mirror (idempotent; skips existing)
```

**rclone remotes** (`~/.config/rclone/rclone.conf` on the server):
- `CloudReve` — WebDAV `https://files.elyesghazel.ch/dav`, user `elyes@elyesghazel.ch`
  (public path; **fine for listing, 413s on big uploads** — don't upload big files
  through it).
- `CloudReveDirect` — same creds, `http://<container-ip>:5212/dav`, maintained by the
  mirror script. Used for the actual uploads.

> Uploading big clips from the **desktop** `CloudReve:` remote (also the public URL)
> will 413 for the same reason — that's why the mirror runs server-side.

---

## Reproduce from scratch

1. `mkdir -p /srv/media/gopro-share` (owned by `elyes`).
2. Add DNS: `share` A → VPS IP, grey-cloud.
3. Drop `docker-compose.yml` + `nginx.conf` in `/opt/docker/gopro-share/` (both in
   the dotfiles repo under `gopro/server/`), `docker compose up -d`.
4. Add `expire.sh` + the hourly cron. Install `python3`, `ffmpeg`, `rclone` on the
   host — the dashboard builder needs all three.
5. Ensure a `CloudReve` WebDAV remote exists in the server's rclone.conf (copy the
   `[CloudReve]` block from the desktop — the obscured password is portable).
6. Add `cloudreve-mirror.sh`; set `CLOUDREVE_SYNC=1` in `~/.config/gopro.conf` on the desktop.
