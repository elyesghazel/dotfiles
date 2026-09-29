# Setting up a machine from these dotfiles

A complete walkthrough, from a bare Arch install to a working Hyprland desktop, plus the
lighter WSL (CLI-only) path. Every secret, key and machine-specific address is kept out of
the repo on purpose. This guide says where each one goes on the machine, never what it is.

- [1. What you end up with](#1-what-you-end-up-with)
- [2. Before you start](#2-before-you-start)
- [3. Clone and review](#3-clone-and-review)
- [4. Run the installer](#4-run-the-installer)
- [5. Per-machine configuration](#5-per-machine-configuration)
- [6. Secrets and accounts](#6-secrets-and-accounts)
- [7. Optional packages](#7-optional-packages)
- [8. WSL (CLI only)](#8-wsl-cli-only)
- [9. Day to day](#9-day-to-day)
- [10. Keeping the repo clean](#10-keeping-the-repo-clean)
- [11. Troubleshooting](#11-troubleshooting)

---

## 1. What you end up with

| Layer | What |
|---|---|
| Session | SDDM → Hyprland (Lua config), Waybar, Dunst, Vicinae launcher, Hypridle/Hyprlock |
| Shell | Fish with a custom two-line prompt, zoxide, pnpm, nvm, uv |
| Terminal | Kitty, JetBrainsMono Nerd Font, Catppuccin Mocha |
| Services | Taildrop inbox drain, CloudReve rclone mount, daily unattended upgrades |
| Tooling | Claude Code with a synced global config, skills and MCP bootstrap |
| Pipelines | GoPro → Jellyfin transcode/share ([`gopro/README.md`](../gopro/README.md)) |

Every top-level directory is a [GNU Stow](https://www.gnu.org/software/stow/) package.
`stow <pkg>` symlinks its contents into `$HOME`, mirroring the path layout:
`kitty/.config/kitty/kitty.conf` → `~/.config/kitty/kitty.conf`.

Three things are **copied, not stowed**, each for a reason:

| What | Why |
|---|---|
| `autoupdate/` | Runs as root, and root must never execute a symlink into a user-writable home |
| `claude/.claude/settings.json` | Claude Code rewrites it atomically, which would replace the symlink with a plain file |
| `gopro/server/` | It's the VPS side, rsync'd there by `gopro share` |

---

## 2. Before you start

You need a working Arch base install:

- a user with `sudo`
- network (NetworkManager or `iwd`, anything that gives you internet)
- `git` and `base-devel`
- a GPU driver that fits the hardware (see below)

```bash
sudo pacman -S --needed git base-devel
```

**GPU drivers are not managed by the package lists.** The lists are an export of whichever
machine last ran `dotsync`, so they may or may not contain a driver, and the one they
contain may be wrong for this machine. Install the right one yourself before continuing:

| Hardware | Packages |
|---|---|
| NVIDIA (Turing or newer, e.g. RTX 20xx/30xx/40xx) | `nvidia-open-dkms nvidia-utils libva-nvidia-driver` + headers for every installed kernel (`linux-headers`, `linux-lts-headers`) |
| AMD / Intel | `mesa vulkan-radeon` or `mesa vulkan-intel` |

The package lists are also only as fresh as the last `dotsync` run. Anything missing
afterwards, install by hand and let the next `dotsync` record it.

---

## 3. Clone and review

```bash
git clone https://github.com/elyesghazel/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

The clone location matters: a few things (`dotsync`, relative stow targets) assume
`~/dotfiles`.

**Read before running.** Some files are tuned for my hardware and will be wrong on yours:

| File | What's specific |
|---|---|
| `hypr/.config/hypr/conf/host.lua` | Monitor names, modes, positions; input sensitivity |
| `hypr/.local/bin/xdph-autopick` | Which monitor screen sharing picks without asking |
| `fish/.config/fish/config.fish` | `EDITOR`, `JAVA_HOME` |
| `fish/.config/fish/host/wsl.fish` | Project paths, corporate CA settings |

These are covered in [section 5](#5-per-machine-configuration). Nothing breaks if you run
the installer first, but the monitor layout will look wrong until you fix `host.lua`.

### Clear the way for stow

Stow refuses to overwrite real files. A fresh install already has some of the files it
wants to link (the default `~/.config/fish/config.fish`, `~/.config/kitty/kitty.conf`, the
Hyprland example config…). Move them aside first:

```bash
cd ~/dotfiles
stow -n -v fish kitty hypr waybar dunst starship vicinae claude systemd 2>&1 | grep 'existing target'
# for each conflicting file:
mv ~/.config/fish/config.fish ~/.config/fish/config.fish.orig
```

`stow -n` is a dry run and changes nothing. Avoid `stow --adopt` unless you know what it
does: it moves *your* file into the repo, overwriting the tracked version.

---

## 4. Run the installer

```bash
./install.sh
```

It asks for your sudo password several times. What it does, in order:

1. **Official packages** from `packages/pacman.txt` (`pacman -S --needed`)
2. **yay**, bootstrapped from the AUR if missing
3. **AUR packages** from `packages/aur.txt`
4. **Claude Code** via npm, installing `nodejs`/`npm` first if needed
5. **pyicloud** via `uv tool install` (skipped if `uv` is missing)
6. **Stow** the core packages: `fish kitty hypr waybar dunst starship vicinae claude systemd`
7. **User services**: `taildrop-inbox`, then creates `/mnt/cloudreve` and enables
   `rclone-cloudreve` (both fail harmlessly until [section 6](#6-secrets-and-accounts) is done)
8. **Unattended upgrades**: `sudo autoupdate/setup.sh` (see [section 9](#unattended-upgrades))
9. **Claude settings**: copies `settings.json`, backing up a differing existing one
10. **MCP servers**: runs `mcp-bootstrap.fish` if `~/.claude/secrets.fish` exists, otherwise
    prints what to do

It's safe to re-run: every step is idempotent (`--needed`, existence checks, stow's own
checks).

Then enable the login manager and the basics, and reboot into Hyprland:

```bash
sudo systemctl enable sddm bluetooth docker
sudo usermod -aG docker "$USER"
chsh -s /usr/bin/fish
reboot
```

Pick the **Hyprland** session in SDDM.

---

## 5. Per-machine configuration

### Monitors and input: `host.lua`

`hypr/.config/hypr/conf/host.lua` is the one place for machine-specific Hyprland settings.
It's loaded last, so it overrides the shared modules. List your outputs:

```bash
hyprctl monitors all | grep -E '^Monitor|availableModes'
```

Then describe them:

```lua
hl.monitor({ output = "DP-1",     mode = "2560x1440@165", position = "0x0",    scale = 1.0 })
hl.monitor({ output = "HDMI-A-1", mode = "1920x1080@60",  position = "2560x0", scale = 1.0 })
```

Anything not listed falls back to `conf/monitor.lua` (preferred mode, auto position).
Apply with `hyprctl reload`. Keep the shared modules in `conf/` generic; if a setting only
makes sense on one machine, it belongs here.

### Screen sharing: `xdph-autopick`

`hypr/.local/bin/xdph-autopick` answers xdg-desktop-portal's "which screen?" question
without showing a dialog. Change the output name to the monitor you want to share:

```sh
echo "[SELECTION]r/screen:DP-1"
```

### Fish

Environment detection is automatic: `config.fish` sources `host/wsl.fish` when
`$WSL_DISTRO_NAME` is set, and `host/arch.fish` otherwise. Put environment-specific paths
and abbreviations there, not in `config.fish`.

Fish universal variables (`fish_variables`: colors, key bindings) are deliberately **not**
tracked, so each machine keeps its own. Install the plugins listed in `fish_plugins`:

```fish
fisher update
```

---

## 6. Secrets and accounts

Nothing in this section is in the repo. Every file created here is either outside the stow
packages or gitignored. Placeholders are written as `<like-this>`.

### Claude Code: MCP servers

MCP servers live in `~/.claude.json`, next to OAuth tokens and machine IDs, so that file is
never synced. The server *definitions* are tracked in `claude/.claude/bin/mcp-bootstrap.fish`;
their credentials go in a local secrets file:

```fish
claude                                                     # log in once
cp ~/.claude/secrets.fish.example ~/.claude/secrets.fish   # gitignored
$EDITOR ~/.claude/secrets.fish                             # fill in real values
fish ~/.claude/bin/mcp-bootstrap.fish                      # idempotent, re-run any time
```

`secrets.fish` also holds the ntfy settings used by `clip`. The example file documents
each variable.

### rclone remotes

Remotes (and their obscured passwords) live in `~/.config/rclone/rclone.conf`, which isn't
part of any stow package. Create them interactively with `rclone config`, or in one go:

```bash
# CloudReve (files) — mounted at /mnt/cloudreve by rclone-cloudreve.service
rclone config create CloudReve webdav url=https://<cloudreve-host>/dav \
    vendor=other user='<login>' pass='<password>' --obscure

# MyCloud — the GoPro originals archive
rclone config create mycloud webdav url=https://webdav.mycloud.ch \
    vendor=other user='<login>' pass='<password>' --obscure

rclone lsd CloudReve:                                 # sanity check
systemctl --user restart rclone-cloudreve
```

The remote name `CloudReve` must match the unit. See
[the rclone section of troubleshooting](#an-app-freezes-when-opening-files-from-mntcloudreve)
for why that unit has aggressive timeouts.

### Tailscale

Used by `send`, `wake`, and the Taildrop inbox.

```bash
sudo systemctl enable --now tailscaled
sudo tailscale up
sudo tailscale set --operator="$USER"                 # lets taildrop-inbox run unprivileged
systemctl --user restart taildrop-inbox
```

Received files land in `~/tailscale-files`. Details: [`device-transfer.md`](device-transfer.md).

### WireGuard (`vpn`)

The config goes in `/etc/wireguard/<iface>.conf` (root-owned, `chmod 600`) and never in
the repo. Get it from whoever runs the WireGuard server. The tunnel is deliberately not
enabled at boot; `vpn` brings it up on demand:

```bash
sudo pacman -S --needed wireguard-tools
sudo install -m600 <your-config>.conf /etc/wireguard/wg0.conf
vpn up && vpn status
```

### Apple Reminders (`remind`, `icloud`)

```fish
icloud auth login --username <apple-id>              # interactive: password + 2FA
```

The session is cached by pyicloud in your home directory, outside the repo.

### GoPro pipeline

```bash
stow gopro
cp ~/dotfiles/gopro/.config/gopro.conf.example ~/.config/gopro.conf   # real file is gitignored
$EDITOR ~/.config/gopro.conf                                           # Jellyfin API key etc.
```

It also needs an SSH alias `server` in `~/.ssh/config` pointing at the VPS. The server side
is documented in [`gopro/jellyfin-server-setup.md`](../gopro/jellyfin-server-setup.md) and
[`gopro/gopro-share-server.md`](../gopro/gopro-share-server.md). Needs an NVIDIA GPU (NVENC).

### Wake-on-LAN (`wake`)

BIOS, NIC and Raspberry Pi setup: [`wake-on-lan.md`](wake-on-lan.md).

---

## 7. Optional packages

Not part of the default stow run:

```bash
stow nwg-dock        # dock → ~/.config/nwg-dock-hyprland/
stow spicetify       # Spotify theme → ~/.config/spicetify/, then: spicetify apply
stow gopro           # see above
```

---

## 8. WSL (CLI only)

No Hyprland, no installer. `install.sh` targets full Arch, so on WSL (an Arch or any
distro with fish) just stow the shell-side packages:

```bash
git clone https://github.com/elyesghazel/dotfiles.git ~/dotfiles && cd ~/dotfiles
sudo pacman -S --needed fish stow starship zoxide git     # or your distro's equivalent
stow fish starship claude
cp claude/.claude/settings.json ~/.claude/settings.json
chsh -s /usr/bin/fish
```

`config.fish` detects WSL and sources `host/wsl.fish`: project path variables,
`cdbiz`/`cdedu`/`cdplay` abbreviations, and settings for corporate TLS interception
(`NODE_EXTRA_CA_CERTS`, `NODE_OPTIONS`). Edit the paths there to match the machine.

Claude Code MCP setup is the same as on Arch ([section 6](#claude-code-mcp-servers)).

---

## 9. Day to day

### Syncing changes

```fish
dotsync "fix(waybar): widen clock pill"      # validated Conventional Commit subject
dotsync                                      # falls back to chore(sync): …
```

`dotsync` refreshes the package lists, copies `settings.json` back into the repo, commits
(tagged with the hostname so several machines can share the repo) and pushes. On a second
machine, `git pull` before editing.

### Packages

```bash
packages/update.sh update     # export explicitly installed packages → lists
packages/update.sh diff       # installed-but-untracked, and tracked-but-missing
packages/update.sh services   # dump enabled units / timers / autostart (for RUNNING.md)
```

### Unattended upgrades

`autoupdate.timer` runs `pacman -Syu`, then `yay -Sua`, once a day, on AC power only,
with sleep and shutdown inhibited while it runs. AUR builds run as a dedicated
`aurbuilder` system user whose only sudo right is `pacman`, so your own sudo still asks
for a password.

- Logs: `journalctl -u autoupdate`
- Edited anything in `autoupdate/`? Re-run `sudo autoupdate/setup.sh`: the files are
  copied into `/etc` and `/usr/local/bin`, not linked.
- A failure (file conflict, an Arch news item that needs manual steps) just fails the
  unit. Fix it by hand with `sudo pacman -Syu`.

**Reboot after a kernel or GPU driver upgrade.** The new userspace driver is live
immediately, but the old kernel module stays loaded until reboot. Until then, OpenGL and
Vulkan apps fail to start. `kernel-modules-hook` keeps the running kernel's modules
usable in the meantime; it can't fix a driver version mismatch. Check whether one is
pending:

```bash
[ "$(cat /sys/module/nvidia/version)" = "$(pacman -Q nvidia-utils | cut -d' ' -f2 | cut -d- -f1)" ] \
  && echo ok || echo "reboot needed"
```

### Reloading without a restart

```bash
hyprctl reload                 # Hyprland
pkill waybar; waybar & disown  # Waybar
stow -R <pkg>                  # re-link a package after adding files to it
systemctl --user daemon-reload # after adding or editing a user unit
```

---

## 10. Keeping the repo clean

This repo is public. The rule: **the repo holds structure, the machine holds secrets.**
Anything with a credential, token, private address or account identity lives in a local
file that's either outside every stow package or gitignored. The repo ships an
`.example` with placeholders where a template helps.

| Local file | Holds | Template in repo |
|---|---|---|
| `~/.claude/secrets.fish` | MCP tokens, ntfy token, Sumry login | `claude/.claude/secrets.fish.example` |
| `~/.claude.json`, `~/.claude/.credentials.json` | Claude OAuth, machine IDs, MCP servers | rebuilt by `mcp-bootstrap.fish` |
| `~/.claude/settings.local.json` | Per-machine permission grants | — |
| `~/.config/gopro.conf` | Jellyfin API key | `gopro/.config/gopro.conf.example` |
| `~/.config/rclone/rclone.conf` | WebDAV logins | commands in [section 6](#rclone-remotes) |
| `/etc/wireguard/*.conf` | VPN private key, endpoint | — |
| `~/.ssh/` | SSH keys, host aliases | — |
| `fish/.config/fish/functions/sc_*.fish`, `claude-sc*.fish` | Work-specific helpers | — (gitignored in place) |

The full ignore rules are in [`.gitignore`](../.gitignore) and
[`claude/.gitignore`](../claude/.gitignore).

When adding something new:

- Read a secret from the environment or a local file; never write the value into a tracked
  file, not even "temporarily".
- Use `<placeholder>` values in examples and docs. Public hostnames of self-hosted
  services are fine; tailnet IPs, LAN addresses, MAC addresses, logins and tokens aren't.
- Check `git diff --cached` before `dotsync` pushes it. A quick scan for the obvious:

  ```bash
  git diff --cached | grep -nIE '(ghp_|gho_|sk-ant|tk_[a-z0-9]{20}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|(token|password|api_?key)\s*[=:]\s*["'"'"']?[A-Za-z0-9_-]{16,})'
  ```

- If a secret does get pushed: **rotate it first**. Rewriting history comes second and
  doesn't help on its own, because forks, clones and caches keep the old commit.

---

## 11. Troubleshooting

### A config symlink turned into a regular file

Some apps save by writing a temp file and renaming it over the original, which replaces
the symlink. Re-link it (and copy your changes into the repo first if you want to keep them):

```bash
stow -R <pkg>
```

### `stow` reports "existing target is neither a link nor a directory"

A real file is in the way. See [Clear the way for stow](#clear-the-way-for-stow).

### An app freezes when opening files from `/mnt/cloudreve`

With `--vfs-cache-mode full`, opening a file blocks until rclone has downloaded it. If the
server accepts the request but never answers, the app sits in uninterruptible I/O (`D`
state), where even `kill -9` doesn't work. That's why `rclone-cloudreve.service` sets
connect and I/O timeouts: a stall now fails with `Input/output error` after about 90s
instead of hanging forever. Apps that reopen recent files on startup (slicers, editors)
are the usual victims.

```bash
journalctl --user -u rclone-cloudreve -f              # what rclone sees
rclone lsf CloudReve:                                 # does listing work?
rclone cat CloudReve:<some-file> | head -c 100        # does downloading work?
fusermount3 -uz /mnt/cloudreve                        # emergency: frees stuck processes
systemctl --user restart rclone-cloudreve
```

If listing works but downloads hang, the problem is on the server side (storage backend or
reverse proxy), not on this machine.

### GPU apps fail right after an update

`Failed to initialize NVML: Driver/library version mismatch`, or Mesa/Zink errors like
`vkEnumeratePhysicalDevices failed`, mean the driver was upgraded and the old kernel
module is still loaded. Wait for `systemctl is-active autoupdate` to stop saying
`activating` (DKMS may still be building), then reboot.

### Waybar or Hyprland looks wrong after pulling

```bash
hyprctl reload
hyprctl configerrors           # Lua errors in the Hyprland config
pkill waybar; waybar           # run in the foreground to see CSS/JSON errors
```

### What is actually running on this machine?

[`RUNNING.md`](../RUNNING.md) is the inventory of services, timers and autostart entries.
