# GoPro → Jellyfin streaming pipeline

Self-hosted workflow to make huge GoPro clips (3 GB+ 4K) instantly watchable from
anywhere, without the minutes-long download. **Requires an Nvidia GPU** for the
transcode (built/used on an RTX 3060 / NVENC), so this realistically runs on the
main desktop only.

## The idea

Every clip exists as two copies; the 1080p copy is then reachable three ways:

| Copy | Lives on | Quality | Purpose |
|------|----------|---------|---------|
| **Original** | MyCloud (WebDAV) | 4K, untouched | archive / full-quality editing |
| **Stream copy** | VPS → Jellyfin | 1080p ~8 Mbps + faststart | instant watching |

The 1080p copy is surfaced through three front-ends, all reading the same files on
the VPS (`/srv/media/gopro`):

| Front-end | URL | For |
|-----------|-----|-----|
| **Jellyfin** | `media.elyesghazel.ch` | browsing / watching |
| **Cloudreve** | `files.elyesghazel.ch` → `GoPro/` | grabbing & editing on the phone |
| **`gopro share`** | `share.elyesghazel.ch/<token>/…` | sending one clip to someone (no account) |

The slowness was never the storage location — it was **download-everything delivery
+ huge raw bitrate**. Fix = transcode to a small, seek-friendly file and serve it
from a media server (Jellyfin) that the client direct-plays. The 4K originals stay
archived on MyCloud; the VPS only ever holds the ~1080p copies.

```
SD card / MyCloud (4K)
        │  rclone (pull originals)
        ▼
  RTX 3060 / NVENC  ── full-GPU: hw-decode → scale → h264_nvenc, +faststart
        │  ~1080p ~8 Mbps (≈7× smaller)
        ▼
   ~/gopro-stream  ── rsync ──▶  server:/srv/media/gopro  ──▶  Jellyfin
                                                  (auto library scan via API)
```

## Components

One command, git-style: **`gopro <subcommand>`**. The dispatcher lives at
`.local/bin/gopro` (the only thing in `PATH`); the workers it calls sit in
`.local/libexec/gopro/` (out of `PATH`, so there's no `gopro-*` clutter).

| `gopro …` | What it does |
|-----------|--------------|
| `import [PATH]` | **Primary flow.** SD card → rclone-copy 4K originals to MyCloud (dated folders) → NVENC 1080p → rsync to VPS → trigger Jellyfin scan → mirror to Cloudreve → offer to wipe card. |
| `share <name> [--4k] [--days N] [--all]` | Hand a clip to someone via a private link. Hard-links the 1080p copy on the server under a random token, prints `https://share.elyesghazel.ch/<token>/<clip>` — no account, auto-expires. `--4k` serves the original instead. |
| `pull <name> [--all] [--to DIR]` | Copy the **1080p** copy from the server to `~/edits` for cutting/censoring before posting. (For 4K use `get`.) |
| `get <name> [--to DIR] [--all]` | Pull the **original 4K** back from MyCloud by name/pattern → `~/Downloads`. For full-quality editing. |
| `stream <SRC│remote:path> <DST>` | Batch transcoder. SRC can be a local dir or an rclone remote (pulls each file to temp, encodes, deletes temp). Used for the one-time backfill of clips already on MyCloud. |
| `scan` | POSTs to Jellyfin `/Library/Refresh`. `import` calls this automatically; run by hand after a manual backfill rsync. |
| `mount` | Mount the GoPro SD card and print its path (reuses the fish `gopro-mount` helper). |

Run `gopro` (or `gopro help`) for the list, `gopro <cmd> -h` for per-command options.

Other files: `.config/gopro.conf.example` (settings template → copy to
`~/.config/gopro.conf`, real file git-ignored), `jellyfin-server-setup.md` (VPS
Jellyfin runbook), `gopro-share-server.md` (VPS sharing runbook — nginx link server
+ Cloudreve mirror).

## One-time setup

1. **Deps (desktop):** `ffmpeg` (with NVENC), `rclone`, `rsync`, Nvidia driver.
2. **MyCloud rclone remote:**
   ```bash
   rclone config create mycloud webdav url=https://webdav.mycloud.ch \
     vendor=other user='you@example.com' pass='WEBDAV_PASS' --obscure
   chmod 600 ~/.config/rclone/rclone.conf
   ```
3. **SSH alias** to the VPS in `~/.ssh/config` (here: `server`).
4. **Config:** `cp gopro.conf.example ~/.config/gopro.conf` and fill in
   `ARCHIVE`, `VPS_TARGET`, and the Jellyfin `JELLYFIN_URL` / `JELLYFIN_KEY`
   (Jellyfin → Dashboard → API Keys).
5. **Server:** follow `jellyfin-server-setup.md` (Jellyfin container behind Traefik,
   library = Home videos at `/media/gopro`). Needs `rsync` installed on the VPS.
6. **PATH:** `fish_add_path ~/.local/bin`.

## Usage

```bash
# Every time you pull the SD card:
gopro import                 # auto-detects the card; does everything

# One-time backfill of clips already on MyCloud:
gopro stream "mycloud:Go Pro" ~/gopro-stream
rsync -avP ~/gopro-stream/ server:/srv/media/gopro/
gopro scan                   # nudge Jellyfin to index them
```

Both `gopro stream` and `rsync` are resumable (skip already-done files), so a killed
run just continues. Run the backfill in `tmux` — it can take a couple of hours
(download-bound by MyCloud's WebDAV, not your fibre).

### Getting a clip back out (editing / TikTok)

Jellyfin shows the 1080p copies; the filename matches the original 1:1.

- **TikTok / social:** just hit **Download** in Jellyfin (web ⋮ menu, or the app) —
  1080p is more than TikTok keeps anyway. No need to touch MyCloud. (Requires the
  user's *"Allow media downloads"* permission in Dashboard → Users.)
- **Cutting / censoring before posting:** pull the 1080p copy straight to `~/edits`
  (faster than the Jellyfin download, and skips the browser):
  ```bash
  gopro pull GX010942         # → ~/edits/GX010942.mp4
  gopro pull wheelie --all    # every match
  ```
- **Full-quality editing:** grab the 4K original from MyCloud by name:
  ```bash
  gopro get GX010598          # exact-ish name seen in Jellyfin → ~/Downloads
  gopro get wheelie           # fuzzy match on the filename
  gopro get GX0106 --all --to ~/edits
  ```

### Sending a clip to someone

```bash
gopro share GX010598          # → https://share.elyesghazel.ch/<token>/GX010598.mp4
gopro share wheelie --all     # share every match
gopro share GX010598 --days 3 # link dies after 3 days (default 14)
gopro share GX010598 --4k     # full-res original instead of the 1080p copy
```

No account for the recipient — they click and download. The clip is **hard-linked**
(not copied) from `/srv/media/gopro` into `/srv/media/gopro-share/<token>/`, so it
costs no extra disk. An nginx container behind Traefik serves it with a forced
download; a cron prunes links past their `.expires` stamp. `--4k` is the exception:
it pulls the original from MyCloud and uploads it, so it's slower. Server side is
documented in `gopro-share-server.md`.

### Editing on the phone (Cloudreve)

With `CLOUDREVE_SYNC=1`, every import also mirrors the 1080p copies into Cloudreve
under `GoPro/` (dated folders). Open the Cloudreve app on `files.elyesghazel.ch`,
download the clip, edit in CapCut/LumaFusion — no PC needed. 1080p is plenty for a
phone edit; the mirror never touches the 4K originals.

## Notes / gotchas

- **Deploy:** `cd ~/dotfiles && stow gopro` symlinks `gopro` into `~/.local/bin`, the
  workers into `~/.local/libexec/gopro/`, and the example into `~/.config`. (If a
  worker ever shows up as a real file instead of a symlink, re-run with
  `stow -D gopro && stow --no-folding gopro`.)
- **Secrets:** `~/.config/gopro.conf` (Jellyfin key) and `~/.config/rclone/rclone.conf`
  (WebDAV password) are **not** committed — only the `.example` is.
- **Jellyfin real-time monitoring is unreliable** for rsync'd files (temp-rename +
  batch arrivals miss inotify), hence the explicit `gopro scan` after upload.
- **No transcoding on the VPS** — files are pre-optimized for direct play; the
  server has no GPU and must never transcode.
- Tunables in `gopro.conf`: `RES` (default 1080), `CODEC` (`h264` for max
  compatibility, `hevc` for ~40% smaller). Encoder ladder: VBR `-cq 23`, ~8 Mbps
  avg / 12 Mbps cap — good for high-motion riding footage.
- **Cloudflare 100 MB upload cap:** `files.elyesghazel.ch` is Cloudflare-proxied,
  which rejects request bodies >100 MB (HTTP 413) — and many 1080p clips are bigger.
  So the Cloudreve mirror uploads **server-side, straight to the Cloudreve container
  over the docker network** (`http://<ip>:5212/dav`), bypassing Cloudflare. Uploading
  big clips through the public URL (or the desktop `CloudReve:` rclone remote) will
  413. See `gopro-share-server.md`.
- **Cloudreve only shows files uploaded *through* Cloudreve** (they get DB rows).
  Dropping files into its storage dir (`/mnt/mycloud`) does nothing — the mirror
  writes via WebDAV for exactly this reason.
- `share.elyesghazel.ch` is **grey-cloud / unproxied** in Cloudflare (direct to the
  VPS), like `media.` — needed so large downloads aren't capped by the proxy.
