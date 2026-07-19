# gopro sharing — VPS side

Server-side runbook for the two "get a clip out" front-ends that sit next to
Jellyfin: **gopro-share** (private download links) and the **Cloudreve mirror**
(phone browsing). The desktop scripts are in `README.md`; this is what lives on the
VPS (`ssh server`, Docker + Traefik, network `traefik_proxy`, entrypoint `https`,
certresolver `cloudflare`).

Everything below reads the same 1080p copies Jellyfin serves, at `/srv/media/gopro`.

---

## 1. gopro-share — private download links

`share.elyesghazel.ch/<token>/<clip>` → a forced download, no account. `gopro-share`
(desktop) hard-links a clip into `/srv/media/gopro-share/<token>/` (same filesystem
as `/srv/media/gopro`, so it costs no disk) and prints the URL.

**DNS:** `share.elyesghazel.ch` A → `159.195.34.0`, **grey-cloud / unproxied** (like
`media.`). Direct-to-VPS is required — Cloudflare's proxy caps downloads/uploads.
(Created via Traefik's `CF_DNS_API_TOKEN` in `/opt/docker/traefik/.env`.)

**Container:** `apps-gopro-share` — plain nginx serving the share dir read-only.
Compose + config at `/opt/docker/gopro-share/`:

- `docker-compose.yml` — `nginx:alpine`, mounts `/srv/media/gopro-share:…:ro` and
  `./nginx.conf`, Traefik router `Host(share.elyesghazel.ch)` → port 80.
- `nginx.conf` — `autoindex off` + `location = / { return 404; }` (tokens are the
  only way in; root and listings reveal nothing); `Content-Disposition: attachment`
  (force download); range requests work (resume / partial fetch).

```bash
cd /opt/docker/gopro-share && docker compose up -d      # (re)deploy
docker exec apps-gopro-share nginx -t && docker exec apps-gopro-share nginx -s reload  # after editing nginx.conf
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
   and rejects bodies >100 MB (HTTP 413); many 1080p clips are bigger. So the mirror
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
3. Drop `docker-compose.yml` + `nginx.conf` in `/opt/docker/gopro-share/`, `docker compose up -d`.
4. Add `expire.sh` + the hourly cron.
5. Ensure a `CloudReve` WebDAV remote exists in the server's rclone.conf (copy the
   `[CloudReve]` block from the desktop — the obscured password is portable).
6. Add `cloudreve-mirror.sh`; set `CLOUDREVE_SYNC=1` in `~/.config/gopro.conf` on the desktop.
