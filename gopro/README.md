# GoPro → Jellyfin streaming pipeline

Self-hosted workflow to make huge GoPro clips (3 GB+ 4K) instantly watchable from
anywhere, without the minutes-long download. **Requires an Nvidia GPU** for the
transcode (built/used on an RTX 3060 / NVENC), so this realistically runs on the
main desktop only.

## The idea

Every clip exists as two copies; the stream copy is then reachable four ways:

| Copy | Lives on | Quality | Purpose |
|------|----------|---------|---------|
| **Original** | MyCloud (WebDAV) | 4K, untouched | archive / full-quality editing |
| **Stream copy** | VPS → Jellyfin | 1440p ~12 Mbps + faststart | instant watching |

| Front-end | URL | For |
|-----------|-----|-----|
| **Jellyfin** | `media.elyesghazel.ch` | browsing / watching |
| **Cloudreve** | `files.elyesghazel.ch` → `GoPro/` | grabbing & editing on the phone |
| **`gopro share`** | `share.elyesghazel.ch/<token>/` | sending clips to someone (no account) |
| **`gopro pull` / `get`** | — | getting a clip back for editing |

The slowness was never the storage location — it was **download-everything delivery
+ huge raw bitrate**. Fix = transcode to a small, seek-friendly file and serve it
from a media server (Jellyfin) that the client direct-plays. The 4K originals stay
archived on MyCloud; the VPS only ever holds the stream copies.

```
SD card / MyCloud (4K HEVC ~108 Mbps)
        │  rclone (pull originals, 8 parallel transfers)
        ▼
  RTX 3060 / NVENC  ── hw-decode → CPU scale → h264_nvenc, +faststart
        │  1440p ~12 Mbps (≈9× smaller), profile-stamped
        ▼
   ~/gopro-stream  ── rsync ──▶  server:/srv/media/gopro  ──▶  Jellyfin
                                                  (auto library scan via API)
```

## Components

One command, git-style: **`gopro <subcommand>`**. The dispatcher lives at
`.local/bin/gopro` (the only thing in `PATH`); the workers it calls sit in
`.local/libexec/gopro/` (out of `PATH`, so there's no `gopro-*` clutter), sharing
`_lib.sh`.

| `gopro …` | What it does |
|-----------|--------------|
| `import [PATH]` | **Primary flow.** SD card → rclone-copy 4K originals to MyCloud (dated folders) → NVENC stream copy → rsync to VPS → trigger Jellyfin scan → mirror to Cloudreve → offer to wipe card. |
| `backfill` | Diff the archive against the server and re-encode whatever is missing or stuck on an older ladder. Batched, resumable, idempotent. `--dry-run --limit N --pattern STR` |
| `share <name> […]` | Private link + web dashboard for one clip or a whole set. `--4k --days N --all --title T` |
| `pull <name>` | Copy the **stream copy** from the server to `~/edits` for cutting/censoring. `--all --to DIR` |
| `get <name>` | Pull the original **4K** back from MyCloud by name/pattern → `~/Downloads`. `--to DIR --all` |
| `transcode <SRC│remote:path> <DST>` | Lower-level batch transcoder for an arbitrary source. `backfill` is what you normally want. |
| `scan` | POSTs to Jellyfin `/Library/Refresh`. `import`/`backfill` call it automatically. |
| `mount` | Mount the GoPro SD card and print its path (reuses the fish `gopro-mount` helper). |

Run `gopro` (or `gopro help`) for the list, `gopro <cmd> -h` for per-command options.

## The encode profile stamp

Every stream copy carries the ladder it was made with in its mp4 `comment` tag:

```
gopro-enc:v2:1440p:h264:cq22
```

The skip-check reads that tag instead of just asking "does the file exist". So:

- a clip already at the current profile is **skipped** — imports and backfills are cheap to re-run;
- change `RES` / `CODEC` / `CQ` / `ENC_VERSION` in `gopro.conf` and every existing
  copy becomes **stale**, and `gopro backfill` will redo exactly those;
- bump `ENC_VERSION` alone to force a re-encode without changing the ladder.

That's what makes "do I re-transcode everything or only new ones?" a non-question:
new clips get the current profile automatically, old ones get it whenever you next
run `gopro backfill`, and nothing is ever encoded twice.

```bash
gopro backfill --dry-run          # what's stale, and what it'd redo
gopro backfill --limit 20         # chip away at it
gopro backfill                    # the lot (run it in tmux)
```

## Sending clips to someone

```bash
gopro share GX010598                       # one clip
gopro share GX010598 GX010942 wheelie      # one link, three clips
gopro share 2026-07-25 --all               # everything from that shoot
gopro share 2026-07-25 --all --no-4k       # …stream copies only, link is instant
gopro share wheelie --days 3               # link dies after 3 days
gopro share GX0109 --all --title "Sunday"  # heading on the dashboard
```

Prints `https://share.elyesghazel.ch/<token>/` — a generated dashboard with poster
thumbnails, in-browser playback (range requests, so seeking works), and a **quality
picker on every clip**:

```
   Download
   ┌─────────┬─────────┐
   │  1440p  │   4K    │
   │ 462 MB  │ 3.7 GB  │
   └─────────┴─────────┘
```

The recipient picks per clip — the stream copy for something they just want on their
phone, the untouched original if they're going to edit it. Labels come from each
file's actual height, so a clip shot in 2.7K says 2.7K rather than guessing. If no
original was staged, the picker collapses to the single rung it has.

No account for the recipient. The whole token dir deletes itself on expiry (default
14 days), taking the staged originals with it.

Stream copies are **hard-linked** from `/srv/media/gopro`, so those cost no disk.
Originals are real copies — the **server** pulls them from MyCloud itself, all of a
share's in one batched `rclone` run (~80 MB/s; per-clip calls only manage ~20, since
`--transfers` parallelises across files). They're staged by default; `--no-4k` skips
them for a big share, `SHARE_4K=0` flips the default, and `DISK_MARGIN_GB` (20 by
default) is the free space staging will never eat into. Server side is documented in
`gopro-share-server.md`; the dashboard generator lives in `server/`.

## Getting a clip back out (editing / TikTok)

Jellyfin shows the stream copies; the filename matches the original 1:1.

- **TikTok / social:** just hit **Download** in Jellyfin (web ⋮ menu, or the app) —
  1440p is more than TikTok keeps anyway. (Requires the user's *"Allow media
  downloads"* permission in Dashboard → Users.)
- **Cutting / censoring before posting:** `gopro pull GX010942` → `~/edits/` —
  faster than the Jellyfin download and it skips the browser.
- **Full-quality editing:** `gopro get GX010598` pulls the 4K original from MyCloud.

## One-time setup

1. **Deps (desktop):** `ffmpeg` (with NVENC), `rclone`, `rsync`, Nvidia driver.
2. **MyCloud rclone remote:**
   ```bash
   rclone config create mycloud webdav url=https://webdav.mycloud.ch \
     vendor=other user='you@example.com' pass='WEBDAV_PASS' --obscure
   chmod 600 ~/.config/rclone/rclone.conf
   ```
3. **SSH alias** to the VPS in `~/.ssh/config` (here: `server`).
4. **Config:** `cp gopro.conf.example ~/.config/gopro.conf` and fill in `ARCHIVE`,
   `VPS_TARGET`, `JELLYFIN_URL` / `JELLYFIN_KEY` (Jellyfin → Dashboard → API Keys).
5. **Server:** follow `jellyfin-server-setup.md` (Jellyfin behind Traefik, library =
   Home videos at `/media/gopro`) and `gopro-share-server.md` (nginx share host +
   Cloudreve mirror). Needs `rsync`, `ffmpeg`, `rclone` and `python3` on the VPS.
6. **PATH:** `fish_add_path ~/.local/bin`.

## Notes / gotchas

- **Deploy:** `cd ~/dotfiles && stow gopro`. (If a worker ever shows up as a real
  file instead of a symlink, re-run with `stow -D gopro && stow --no-folding gopro`.)
  `server/` is not stowed — `gopro share` rsyncs it to the VPS on every run, so the
  deployed dashboard generator can't drift from the repo copy.
- **Secrets:** `~/.config/gopro.conf` (Jellyfin key) and `~/.config/rclone/rclone.conf`
  (WebDAV password) are **not** committed — only the `.example` is.
- **MyCloud throttles per connection, not per account.** One stream gets ~4 MB/s;
  eight get **~25 MB/s from the desktop and ~83 MB/s from the VPS**. Every archive
  read goes through `gopro_rclone_fast` (`--transfers 8 --multi-thread-streams 4`),
  tunable via `RCLONE_*` in `gopro.conf`. This is why a full backfill is an evening
  and not a weekend — and why `share --4k` runs server-side.
- **Never use `-hwaccel_output_format cuda` + `scale_cuda` here.** GoPros mounted
  upside down record `rotation=-180` metadata rather than flipping pixels; keeping
  frames on the GPU skips ffmpeg's auto-rotation and bakes the clip in upside down.
  `_lib.sh` decodes on the GPU but scales on the CPU for exactly this reason. It
  costs ~15% encode time and the encode is never the bottleneck (~4.5× realtime at
  1440p on a 3060).
- **1440p is nearly free.** Measured on 60 s of 4K HEVC source: 1080p → 12 s / 79 MB,
  1440p at the same cap → 14 s / 79 MB, 1440p at 12M/18M → 14 s / 131 MB. The old
  1080p ladder was already pinned to its `maxrate`, so most of the extra pixels cost
  encode time rather than bitrate.
- **Jellyfin real-time monitoring is unreliable** for rsync'd files (temp-rename +
  batch arrivals miss inotify), hence the explicit `gopro scan` after upload.
- **No transcoding on the VPS** — files are pre-optimized for direct play; the
  server has no GPU and must never transcode. It only ever does ffprobe + a poster
  frame for the share dashboard.
- **Keep `CODEC=h264`** unless you stop using the share dashboard: hevc is ~40%
  smaller but doesn't play in a plain `<video>` on Firefox or on Linux Chrome.
- **Cloudflare 100 MB upload cap:** `files.elyesghazel.ch` is Cloudflare-proxied and
  rejects request bodies >100 MB (HTTP 413). The Cloudreve mirror therefore uploads
  **server-side, straight to the Cloudreve container over the docker network**.
  `share.` and `media.` are **grey-cloud / unproxied** so large downloads aren't
  capped by the proxy. See `gopro-share-server.md`.
- **Cloudreve only shows files uploaded *through* Cloudreve** (they get DB rows).
  Dropping files into its storage dir does nothing — the mirror writes via WebDAV.
