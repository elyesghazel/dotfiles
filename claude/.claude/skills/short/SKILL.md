---
name: short
description: Make a durable short link on s.elyesghazel.ch with the `short` CLI on the VPS (self-hosted Shlink). Use whenever a link is meant for other people - something to share, post, put in a bio, send to a client or a friend, print on a label or QR code - or whenever a link has to outlive its target and be repointed later ("give me a short link", "shorten this", "make a link I can share", "link for my bio", "repoint s.elyesghazel.ch/x"). Also for listing, repointing, deleting or checking visit stats of short links. NOT for private previews of agent work - that is `show`.
---

# short: durable links on s.elyesghazel.ch

`short` runs on the VPS (`elyes-ghazel-server`, `~/.local/bin/short` -> `/opt/docker/shlink/bin/short`).
From another machine: `ssh server-ts short ...`.

```sh
short https://elyesghazel.tech/zunder/ zunder --title "zunder"   # -> https://s.elyesghazel.ch/zunder
short https://example.com/long/path                              # random 5-char slug, reuses an existing one
short https://new-target.example zunder                          # existing slug + new URL = repoint
short https://example.com/promo promo --expires 30d              # 30d / 12h / 2w / ISO date
short edit <slug> <new-url>
short ls                  # slug, human visits, target, title, expiry
short stats <slug>        # totals + last 10 visits (date, referrer, UA; no IPs stored)
short rm <slug>           # refused above 15 visits - repoint instead
```

Stdout is only the short URL, so `url=$(short ...)` works.

## When to use it

- A link someone else will open: a post, a bio, a message, a QR code, a printed label.
- Anything that should survive a move. `.tech` expires in 2027, `.ch` is permanent: when
  sharing something hosted on `.tech` (a public `show` site, the zunder page), share the
  `s.elyesghazel.ch` link, never the `.tech` URL itself.
- Agent work meant for other people: publish it (`show ... --public`, or wherever it lives),
  then wrap the URL with `short` and hand out the short link.

## When not to

- Private previews for Elyes himself - use `show` and give him that link directly.
- Anything behind login, secrets, or personal data. Short links are public and guessable.

## Notes

- Pick readable slugs (`zunder`, `slideplate-sale`), lowercase with dashes. Re-running with a
  slug that already exists repoints it, so check `short ls` before reusing a name.
- Bare `s.elyesghazel.ch` and unknown slugs redirect to `elyesghazel.ch`.
- Redirects are 302 without caching, so repointing takes effect immediately.
- Service, API key, backup: `/opt/docker/shlink/README.md`.
