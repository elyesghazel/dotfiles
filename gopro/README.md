# GoPro → Jellyfin streaming pipeline

Self-hosted workflow to make huge GoPro clips (3 GB+ 4K) instantly watchable from
anywhere, without the minutes-long download. **Requires an Nvidia GPU** for the
transcode (built/used on an RTX 3060 / NVENC), so this realistically runs on the
main desktop only.

## The idea

Two copies of every clip, two homes:

| Copy | Lives on | Quality | Purpose |
|------|----------|---------|---------|
| **Original** | MyCloud (WebDAV) | 4K, untouched | archive / editing |
| **Stream copy** | VPS → Jellyfin | 1080p ~8 Mbps + faststart | instant watching |

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

| File | What it does |
|------|--------------|
| `.local/bin/gopro-import` | **Primary flow.** SD card → rclone-copy 4K originals to MyCloud (dated folders) → NVENC 1080p → rsync to VPS → trigger Jellyfin scan → offer to wipe card. |
| `.local/bin/gopro-stream` | Batch transcoder. `gopro-stream <SRC│remote:path> <DST>`. SRC can be a local dir or an rclone remote (pulls each file to temp, encodes, deletes temp — no need to hold all originals locally). Used for the one-time backfill of clips already on MyCloud. |
| `.local/bin/gopro-scan` | POSTs to Jellyfin `/Library/Refresh` so new uploads appear without a manual rescan. `gopro-import` calls this automatically; run it by hand after a manual backfill rsync. |
| `.config/gopro.conf.example` | Settings template → copy to `~/.config/gopro.conf` (real file is git-ignored; holds the Jellyfin API key). |
| `jellyfin-server-setup.md` | Runbook for the VPS side (Docker Jellyfin behind Traefik). |

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
gopro-import                 # auto-detects the card; does everything

# One-time backfill of clips already on MyCloud:
gopro-stream "mycloud:Go Pro" ~/gopro-stream
rsync -avP ~/gopro-stream/ server:/srv/media/gopro/
gopro-scan                   # nudge Jellyfin to index them
```

Both `gopro-stream` and `rsync` are resumable (skip already-done files), so a killed
run just continues. Run the backfill in `tmux` — it can take a couple of hours
(download-bound by MyCloud's WebDAV, not your fibre).

## Notes / gotchas

- **Deploy:** `cd ~/dotfiles && stow gopro` symlinks the scripts into `~/.local/bin`
  and the example into `~/.config`.
- **Secrets:** `~/.config/gopro.conf` (Jellyfin key) and `~/.config/rclone/rclone.conf`
  (WebDAV password) are **not** committed — only the `.example` is.
- **Jellyfin real-time monitoring is unreliable** for rsync'd files (temp-rename +
  batch arrivals miss inotify), hence the explicit `gopro-scan` after upload.
- **No transcoding on the VPS** — files are pre-optimized for direct play; the
  server has no GPU and must never transcode.
- Tunables in `gopro.conf`: `RES` (default 1080), `CODEC` (`h264` for max
  compatibility, `hevc` for ~40% smaller). Encoder ladder: VBR `-cq 23`, ~8 Mbps
  avg / 12 Mbps cap — good for high-motion riding footage.
