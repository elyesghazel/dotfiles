# GoPro sharing gallery

`share.elyesghazel.ch/<token>/` serves temporary clip collections through nginx.
`gopro-share-page.py` renders each collection's `.meta.json` as its `index.html`
in the shared elyesghazel design (JetBrains Mono, `//` section labels, `eg.` favicon,
light/dark via the `theme.js` contract).

The design files are served same-origin under `/_eg/`: compose mounts
`/opt/docker/design/public` read-only, so a share page never depends on
design.elyesghazel.ch being up and picks up design changes after `design/sync.sh`.
`static/404.html` is the branded page for expired, unknown and mistyped links (and 403s).
Tokens are `[A-Za-z0-9]+`, so `/_eg/` and `/_share/` can never collide with one.

Recipients get: in-browser playback in a player with prev/next, arrow keys and
autoplay of the next clip, `#clip-N` deep links, per-clip downloads (stream copy and
staged 4K original), a "download all" button, stats (clips, runtime, size) and a
live expiry countdown. Open Graph tags give WhatsApp/iMessage a poster preview.
Playback uses `v/`; forced downloads use `dl/v/` and `dl/4k/`. Keep these routes
separate so browser playback and seeking keep working.

Access is **anyone with the link**, not per-person approval. The root is hidden,
metadata is denied by nginx, and `expire.sh` removes expired token directories hourly.

The source lives in `~/dotfiles/gopro/server/` (page renderer, builder, nginx.conf,
compose, static/). The desktop `gopro share` command rsyncs the builder and renderer
on each run, so commit and push dotfiles and pull on the PC/laptop. nginx.conf,
compose and static/ are copied here by hand. No container rebuild is needed when
changing the renderer: newly built shares use it immediately. To refresh existing
pages: `python3 gopro-share-page.py <dir>/.meta.json > <dir>/index.tmp && mv <dir>/index.tmp <dir>/index.html`.
