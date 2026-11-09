---
name: t3-share
description: Share a T3 Code thread live with someone who has no T3 access (a friend, a client) as a public page in the elyesghazel design, with a short link. Use when the user types /t3-share or says "share this thread/chat", "so my friend can watch it", "make a live page of the <X> thread", "share the t3 chat for <X>", or asks to stop/remove such a share.
---

# t3-share: a live public page for a T3 thread

T3 threads only open for paired devices. `t3-share` (VPS, `~/src/t3-share`, on PATH) mirrors a
thread to `lab.elyesghazel.tech/t3/<slug>/` every 4 s and makes `s.elyesghazel.ch/<slug>`.
The page shows the prompt, agent replies, thinking, every command/edit (tap to open, diffs
coloured), helper agents as nested cards, and images/videos the agent made. Shared design
(JetBrains Mono, `//` labels, dark/light), works on phones.

## Steps

1. **Find the thread.** If the user names it by topic, run `t3-share start "<title words>"`
   directly; if several match it exits and lists ids. Never pick the current share thread
   itself. `t3_thread_list` / `t3_thread_search` also work for finding ids.
2. **Start it:**
   ```sh
   t3-share start <thread-id> --name <short-slug>      # public, 7 days, follows 12 h after idle
   ```
   Options: `--ttl 30d`, `--follow 24h`, `--login` (only Elyes), `--gate` (GitHub sign-in, then
   `gate grant <login> lab/t3/<slug>`), `--worktree DIR` if the agent works outside its thread folder.
   The output JSON has `link` (short) and `page`.
3. **Check** `curl -s -A t3-share-check <page>data.json` returns the title and steps. For a
   visual check: `~/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell --no-sandbox --window-size=390,1600 --virtual-time-budget=6000 --screenshot=<scratchpad>/p.png <page>`.
4. **Reply** with the short link, what the friend sees, when it stops and how to take it down.

## Manage

```sh
t3-share ls                  # slug, unit state, link, title
t3-share stop <slug>         # stop syncing + remove the page (--keep leaves the page up)
t3-share once <slug>         # re-copy page/ + design after editing the template
show ttl t3/<slug> 30d       # keep the page longer
```

## Privacy

The engine replaces `$HOME` with `~`, the agent scratchpad path with `scratchpad`, token-like
strings with `[redacted]`, and cuts long tool output. It still shows the full prompt and every
command. Before sharing a thread that touched secrets, mail, finances or Elyes' private infra,
grep `data.json` for names, emails, IPs and keys and tell him what you found. Friend threads
(his friend's prompt on his account) are fine to share whole.

## Notes

- Public lab pages are CSP-sandboxed, so the design files are vendored next to the page.
- Sync is a transient user unit `t3-share-<slug>` (gone after reboot: run `t3-share start` again,
  same slug keeps the same link).
- `--models DIR` on `t3-share.py` mirrors per-model frame exports (used for the Roblox pet 3D viewer).
