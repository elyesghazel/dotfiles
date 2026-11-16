---
name: waitfor
description: Set a temporary watcher on the VPS for something we're waiting on - a reply or approval mail, a GitHub PR/issue changing (merged, closed, reviewed, new comment), a web page changing or showing/losing some text, or any shell check (a deploy, a release, a CI run, a package version) - and get an ntfy push on Elyes' phone when it happens. Use whenever a task ends with "now we wait" (applied somewhere, sent a request, waiting for approval/review/delivery/DNS/a build), when he says "tell me when", "let me know when", "watch for", "ping me if", "keep an eye on", "notify me when", or asks what we're still waiting on. Also for listing or stopping watches.
---

# waitfor

`waitfor` (`~/agents/waitfor/waitfor.py`, on PATH) keeps small temporary watches in
`~/.local/state/waitfor/watches.json`. Cron (`agents run waitfor check`, every 5 min, entry
`waitfor` in `~/agents/automations.yaml`) runs the ones that are due. A hit pushes to ntfy topic
`agents`, with the `--note` as the next step, and stops the watch. If nothing happens before
`--for` runs out, it pushes "gave up" and stops. Three failed checks in a row push a warning.

Set one, without asking, whenever we start waiting on something outside our control.
Then tell him in one line what's being watched and until when.

```
waitfor mail  signpath-reply --from signpath --for 30d --note "set up SignPath project + repo secrets (zunder #27)"
waitfor gh    pr-235 hyprland-community/awesome-hyprland#235 --note "merged? update the README badge"
waitfor url   aur-halo https://aur.archlinux.org/packages/halo --contains "0\.2\.0"
waitfor url   page-change https://example.com/status            # any change of the page
waitfor cmd   dns-ok 'dig +short shop.slideplate.ch | grep -q 1.2.3.4' --ok --every 15m --for 2d
waitfor cmd   release 'gh release view -R elyesghazel/zunder --json tagName -q .tagName'   # output changes

waitfor ls [--all]      waitfor rm NAME      waitfor test NAME (dry run)      waitfor check NAME (run now)
```

Options for every kind: `--every 10m` (5m minimum), `--for 14d`, `--note "next step"`,
`--click URL` (what the push opens; url and gh watches default to the page),
`--then 'SHELL'` (runs on a hit, e.g. `draft add ...` or `remind ...`; never sends mail or
anything public), `--keep` (keep watching after a hit).

Rules:
- `mail` only counts mail that arrives after the watch was set. It searches every folder except
  Junk and Trash. Match on the sender's domain (`--from signpath`) rather than an exact address.
- `cmd` checks run as elyes on the VPS with a 2 min timeout. Keep them read-only and cheap, and
  never wake the PC (`ssh arch`) from one.
- Name a watch after what it waits for (`signpath-reply`, `pr-235`). The note should say what to do
  next, so the push alone tells him or the next session how to continue.
- When he asks what we're waiting on, or a session picks up an older task, run `waitfor ls --all`.
  A finished watch keeps what it saw in `hit_detail` in the state file.
