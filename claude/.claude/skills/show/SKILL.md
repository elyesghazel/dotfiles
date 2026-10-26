---
name: show
description: Publish something for Elyes to look at as a web page on lab.elyesghazel.tech/<path>/ (the agent hub) with the `show` CLI on the VPS. Use whenever you built a page, report, mockup, UI preview, chart, rendered video, gallery or a running dev server that he should open on his phone or laptop — "show me", "send me a link", "let me see it", "put it online", "preview this", "can I look at it on my phone" — and proactively at the end of work whose result is visual. Also for listing or removing what is published.
---

# show: the agent hub on elyesghazel.tech

`show` runs on the VPS (`elyes-ghazel-server`, `~/.local/bin/show` → `/opt/docker/lab/bin/show`).
From another machine, copy the files to the VPS first (`scp` / `rsync` to `server-ts`) and run
`show` there over ssh.

```sh
show ./dist --name sumry/redesign --title "Sumry overview redesign"   # folder → lab.elyesghazel.tech/sumry/redesign/
show report.html --name server/audit --title "Security audit"        # one file → index.html
show clip.mp4 --name slideplate/clip --ttl 2d                        # any file, listed by nginx
show --port 5173 --name sumry/staging --title "Sumry staging"        # proxy → sumry-staging.elyesghazel.tech
show ls               # what is live
show rm <path>        # take it down (e.g. show rm sumry/redesign)
show ttl <path> 30d   # change the expiry of a live site (or `never`)
```

It prints the URL. No ntfy note by default: put the link in your reply instead.
lab.elyesghazel.tech lists everything that is live.

## Rules

- **Private by default.** Every site sits behind the Pocket ID passkey login (tinyauth, `sso-tech`).
  Use `--public` only when the page is meant for other people (a demo for a client, a link to
  share) and contains nothing personal. Finances, health, vault notes, credentials, server
  internals: never `--public`.
- **Sharing with specific people:** `--gate` instead of `--public` puts the site behind Elyes
  Sign-in (GitHub login, login.elyesghazel.tech); then `gate grant <github-login> lab/<path>`.
  A parent path shares the whole folder (`gate grant <login> lab/schule/rega`), but only its
  `--gate` sites: private ones stay private. Only when Elyes names who should see it.
- **Expiry: pick it yourself, every time.** Don't just take the default; set `--ttl` by what it is:
  | What | `--ttl` |
  |---|---|
  | quick check, screenshot-like preview, dev server proxy | `1d` (or `12h`) |
  | mockup, report, research he'll come back to this week | `7d` (default) |
  | reference material, a plan or overview he'll use for a while | `30d` |
  | something he explicitly wants to keep | `never` |
  Change it later with `show ttl <path> <ttl>` (e.g. he says "keep that" → `show ttl <path> never`).
  He can also delete a site or change its expiry himself from the buttons on lab.elyesghazel.tech.
  A cron runs `show gc` every 5 minutes. The domain is a 1-year GitHub Student Pack domain: anything
  meant to last for years belongs on `.ch`. Permanent tools (like the ops dashboard at
  `ops.elyesghazel.tech`) are real services in `/opt/docker`, not `show` sites.
- **Paths: always pass `--name` and group by what it belongs to.** Up to 4 segments of
  lowercase `a-z0-9-`, e.g. `schule/rega/lernvideo`, `slideplate/text-plates`,
  `zunder/logo`, `sumry/redesign`. Reuse an existing folder when the thing relates to one
  (`show ls` lists them); a one-off with no home can stay top-level. Every folder gets a
  listing page (`lab.elyesghazel.tech/schule/rega/`). A site can't sit inside another site.
  Re-running with the same `--name` replaces the site. Without `--name` it derives a
  top-level name from the file or folder. Reserved first segment: `api`.
- **`--port` keeps a subdomain** (the path with dashes: `sumry/staging` →
  `sumry-staging.elyesghazel.tech`), because dev servers expect to live at `/`.
- **`--port` servers must bind `172.22.0.1`** (the traefik_proxy gateway), e.g.
  `vite --host 172.22.0.1 --port 5173`. Never bind `0.0.0.0`: the VPS has no inbound
  firewall, so that would expose the server on the public IP, bypassing the login.
  `show rm` the proxy when the server stops.
- Pages are self-contained static files. **Use relative asset paths only** (`img/a.png`,
  `../index.html`): a root-absolute `/style.css` points at the lab root, not the site. There
  is no server-side code; for anything dynamic use `--port`.
- `--public` sites are served with a CSP sandbox (they share the lab origin with private
  sites): scripts, forms, popups and fetches of files next to them work, `localStorage` and
  cookies don't.
- `--notify` sends a ntfy note with a tap-to-open link to topic `agents`. Only use it when he
  explicitly asks for a push, or for unattended runs (cron, routines) where nobody reads the reply.
- Inside T3 Code, `html_render` is still the way to show something *in the chat*. `show` is for
  a link he opens elsewhere, keeps for a few days, or looks at on his phone.

## How it fits together

- `*.elyesghazel.tech` → wildcard DNS and cert → Traefik. The fallback router `lab`
  (`/opt/docker/traefik/data/dynamic/lab.yml`, priority 1) sends lab and every unknown
  subdomain to `web-lab` (nginx, `/opt/docker/lab`) behind `sso-tech@docker`. nginx serves
  `lab.elyesghazel.tech/<path>/` and 301s old `<slug>.elyesghazel.tech` links to their path.
- Public and gated paths and `--port` proxies get their own `lab-<path with _>.yml` route
  file next to it. Traefik watches that directory, so there is no restart.
- Login: `auth.elyesghazel.tech` (tinyauth) → `id.elyesghazel.ch` (Pocket ID, passkeys).
- The hub buttons post to `web-lab-api` (`/opt/docker/lab/api/server.py`), which imports
  `bin/show`; manifest writes are serialised with a flock on `/opt/docker/lab/.lock`.
- State lives in `/opt/docker/lab/manifest.json` (keyed by path), sites in `/opt/docker/lab/sites/<path>`.
  ntfy settings are in `~/.config/show/config.env`.
