# Getting files and text to other devices

Goal: push something to the phone, the laptop or the desktop **only when asked** —
no sync folder, no background daemon watching directories, nothing to configure
per device pair beyond the tailnet that already exists.

Two commands, split by what is being moved:

| What                          | Command                     | Transport                         |
| ----------------------------- | --------------------------- | --------------------------------- |
| files, photos, PDFs, archives | `send <host> <files...>`    | Taildrop (WireGuard, peer-to-peer) |
| text to *paste* on the phone  | `clip <text>` / `... \| clip` | ntfy notification                  |

Why two: Taildrop only delivers **files**. Piping the clipboard through it lands as a
`.txt` in the phone's Files app, which is the wrong shape for a URL or a code you want
to paste right away. A notification is copyable with one long-press.

```
laptop ──tailnet/Taildrop──▶ iPhone / Pixel      files pop up in the Tailscale app
laptop ──tailnet/Taildrop──▶ elyes-arch          files land in ~/tailscale-files
laptop ──https──▶ ntfy.elyesghazel.ch ──push──▶ phone      text, one tap to copy
```

Both live in `fish/functions/` (`send.fish`, `clip.fish`); `send` has tab completion
for online peers.

---

## `send` — files over Taildrop

```sh
send elyes-iphone photo.jpg report.pdf    # push files
wl-paste | send pixel-9 note.txt          # push stdin as a named file
send --targets                            # who can receive right now
send --get [dir]                          # manual inbox drain (see below)
```

`send <Tab>` completes online tailnet hostnames (this machine excluded), then files.

### Receiving on a phone

Nothing to do. iOS/Android show the transfer in the Tailscale app; on iOS the file
goes to Files → Tailscale, on Android to Downloads.

### Receiving on Linux — the inbox

Linux has no Taildrop UI. `tailscaled` stores incoming files in
`/var/lib/tailscale/files/<user>/`, which is **root-owned, 0700, and contains
half-written transfers**, so it cannot be symlinked or read directly. Files must be
moved out with `tailscale file get`.

The `systemd` stow package does that continuously:

```
systemd/.config/systemd/user/taildrop-inbox.service
  → tailscale file get --loop --wait --conflict=rename ~/tailscale-files
```

Once enabled, anything Taildropped to the machine appears in `~/tailscale-files` within
a second. `send --get` exists for boxes without the service.

### Setup, once per Linux machine

```sh
sudo tailscale set --operator=$USER          # tailscale CLI without sudo
cd ~/dotfiles && stow fish systemd
systemctl --user daemon-reload
systemctl --user enable --now taildrop-inbox
```

`install.sh` does the stow + enable; the `--operator` line is the only manual step.

---

## `clip` — text to the phone over ntfy

```sh
clip https://example.com/some/path        # arguments are the text
wl-paste | clip                           # piped
clip                                      # no args, no pipe → reads the desktop clipboard
```

`clip` takes **no host** — it always goes to the phone. Everything after it is the
message (`clip elyes-iphone` sends the words "elyes-iphone").

Posts to the self-hosted ntfy at `https://ntfy.elyesghazel.ch`, topic `clip`, as the
write-only user `clip` (server is `deny-all` by default; see `/opt/docker/ntfy/README.md`
on the VPS). The title carries the sending machine's hostname.

### Setup

1. Credentials in `~/.claude/secrets.fish` (gitignored, template in
   `claude/.claude/secrets.fish.example`):

   ```fish
   set -gx NTFY_URL   "https://ntfy.elyesghazel.ch"
   set -gx NTFY_TOPIC "clip"
   set -gx NTFY_TOKEN "tk_..."       # docker exec apps-ntfy ntfy token list clip
   ```

2. Phone: ntfy app → subscribe to `clip` on `ntfy.elyesghazel.ch` (the app's `elyes`
   login can read every topic). Messages are cached 72 h server-side, so a clip sent
   while the phone was offline still arrives.

### Gotchas that shaped `clip.fish`

- **fish 4: a `(command substitution)` inside a function does not see piped stdin.**
  `set text (cat)` is always empty; use `read -z text`.
- `read -l` inside an `if` block is scoped to that block — declare the variable
  outside and `read` without `-l`.
- Arch has no `hostname` binary (it's in `inetutils`); use fish's `$hostname`.
- `curl -d` strips newlines; `--data-binary` keeps them (same rule as the daily brief).

---

## Not chosen

- **Syncthing / Nextcloud / obsidian-sync for files** — continuous sync; the point
  here is that nothing moves unless asked.
- **LocalSend** — works, but adds a second discovery layer (mDNS) for devices that
  already see each other on the tailnet, and needs its app open on both ends.
- **KDE Connect** — real clipboard sync, but Android-only in practice and Plasma-shaped;
  ntfy already exists and the phone is already subscribed to it.
