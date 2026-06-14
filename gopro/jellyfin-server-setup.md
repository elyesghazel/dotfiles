# Jellyfin Setup Runbook (for Claude on `elyes-ghazel-server`)

**Goal:** stand up Jellyfin to stream pre-transcoded 1080p GoPro clips at
`https://media.elyesghazel.ch`. The fat 4K originals stay on MyCloud; this server
only ever holds the small streamable copies, which arrive via `rsync` from Elyes'
desktop into `/srv/media/gopro`.

You are running **on the server** as user `elyes` (uid/gid likely 1000), with sudo.
Do not invent values — the ones below were discovered from the live host. Verify
before relying on them, and ask Elyes only if something contradicts this doc.

---

## Known environment (already verified)

| Thing | Value |
|-------|-------|
| Docker | 29.5.3, working |
| App layout | each stack in `/opt/docker/<name>/` (e.g. `/opt/docker/cloudreve`, `/opt/docker/traefik`) |
| Reverse proxy | `inf-traefik` (traefik:latest) |
| **Traefik network** | `traefik_proxy` (external; apps join this) |
| Traefik entrypoint | `https` |
| TLS cert resolver | `cloudflare` (`tls=true`) |
| Free disk | ~350 GB on `/` (`/srv` lives here) |
| Existing label style | see Cloudreve example below |

Cloudreve's working Traefik labels (copy this pattern exactly):
```
traefik.enable=true
traefik.http.routers.cloudreve.entrypoints=https
traefik.http.routers.cloudreve.rule=Host(`files.elyesghazel.ch`)
traefik.http.routers.cloudreve.tls=true
traefik.http.routers.cloudreve.tls.certresolver=cloudflare
traefik.http.services.cloudreve.loadbalancer.server.port=5212
```

---

## Step 0 — re-verify before changing anything
```bash
docker ps --filter name=traefik
docker network inspect traefik_proxy >/dev/null && echo "traefik_proxy OK"
id elyes                      # note UID:GID — used for file ownership below
```

## Step 1 — create directories
```bash
sudo mkdir -p /opt/docker/jellyfin/{config,cache}
sudo mkdir -p /srv/media/gopro
# Owned by elyes so the desktop's rsync can write, and Jellyfin (run as elyes) can read.
sudo chown -R elyes:elyes /opt/docker/jellyfin /srv/media
```

## Step 2 — write the compose file
Create `/opt/docker/jellyfin/docker-compose.yml`. Replace `UID:GID` with the numbers
from `id elyes` (almost certainly `1000:1000`):

```yaml
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: apps-jellyfin          # matches the apps-* naming convention
    user: "1000:1000"                      # <-- from `id elyes`
    networks: [traefik_proxy]
    volumes:
      - ./config:/config
      - ./cache:/cache
      - /srv/media/gopro:/media/gopro:ro   # streamable copies, read-only
    environment:
      - JELLYFIN_PublishedServerUrl=https://media.elyesghazel.ch
    restart: unless-stopped
    labels:
      - traefik.enable=true
      - traefik.docker.network=traefik_proxy
      - traefik.http.routers.jellyfin.rule=Host(`media.elyesghazel.ch`)
      - traefik.http.routers.jellyfin.entrypoints=https
      - traefik.http.routers.jellyfin.tls=true
      - traefik.http.routers.jellyfin.tls.certresolver=cloudflare
      - traefik.http.services.jellyfin.loadbalancer.server.port=8096

networks:
  traefik_proxy:
    external: true
```

## Step 3 — DNS for `media.elyesghazel.ch`
Add a record in Cloudflare pointing to this server (`159.195.34.0`).

> **Important — streaming + Cloudflare:** the orange-cloud (proxied) mode buffers
> and time-limits large media and is discouraged for video. **Prefer DNS-only
> (grey cloud)** for `media.` so playback streams straight from Traefik. Note this
> exposes the origin IP. If Elyes insists on proxying, keep it but expect possible
> buffering on longer clips. Confirm the choice with Elyes if unsure.
> (Cert resolver `cloudflare` uses DNS-01, so HTTPS works either way.)

## Step 4 — launch
```bash
cd /opt/docker/jellyfin
docker compose up -d
docker logs -f apps-jellyfin   # watch until "Startup complete"; Ctrl-C to stop tailing
```

## Step 5 — first-run wizard
Open `https://media.elyesghazel.ch`:
1. Create the admin account (give Elyes the credentials).
2. **Add Media Library** → type **Home videos** → folder `/media/gopro`.
3. In that library's settings enable **"Enable real-time monitoring"** so newly
   rsynced clips appear automatically.
4. Dashboard → Playback: leave hardware transcoding **off** (files are pre-optimized
   1080p H.264 → clients direct-play; this server has no GPU and must not transcode).

## Step 6 — verify
```bash
docker inspect apps-jellyfin --format '{{json .State.Health}}{{println}}'   # if healthcheck present
docker network inspect traefik_proxy --format '{{range .Containers}}{{.Name}} {{end}}' | tr ' ' '\n' | grep jellyfin
curl -sI https://media.elyesghazel.ch | head -3
```
Then play a clip from the web UI and confirm it starts in ~1–2 s with no
server-side transcode (Dashboard → Activity should show **Direct Play**).

---

## How new clips arrive (context, no action needed)
Elyes runs `gopro-import` on his desktop. It rsyncs 1080p copies to
`server:/srv/media/gopro/<date>/…`. With real-time monitoring on (Step 5.3),
Jellyfin indexes them within seconds. If a manual rescan is ever needed:
`Dashboard → Scheduled Tasks → Scan All Libraries`, or via API.

## Notes / hardening
- Back up `/opt/docker/jellyfin/config` (it holds users, metadata, watch state).
- Don't put 4K originals here — `/srv` is only ~350 GB and originals live on MyCloud.
- If you want auth in front later, add a Traefik forward-auth middleware; Jellyfin's
  own login is fine for a personal instance.
- Keep the image current: `docker compose pull && docker compose up -d`.
