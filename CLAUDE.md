# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Arch Linux dotfiles managed with **GNU Stow**. Each top-level directory is a stow package that symlinks into `$HOME`. The repo targets two environments: full Hyprland desktop (Arch) and headless CLI (WSL).

## Key commands

```bash
# Apply a package (symlink into ~/)
stow <package>             # e.g. stow hypr, stow waybar

# Remove a package's symlinks
stow -D <package>

# Sync dotfiles to git (updates package lists, commits, pushes)
dotsync                    # fish function — run inside a fish shell

# Update package tracking lists
./packages/update.sh update   # exports pacman -Qqen / -Qqem to packages/*.txt
./packages/update.sh diff     # shows what's installed but untracked and vice versa

# Full system update (pacman + AUR + pnpm + dotsync)
update_all                 # fish function

# Reload configs without restarting
hyprctl reload             # Hyprland
pkill waybar; waybar &     # Waybar
```

## Repo structure

```
dotfiles/
├── hypr/        → ~/.config/hypr/
├── waybar/      → ~/.config/waybar/
├── kitty/       → ~/.config/kitty/
├── fish/        → ~/.config/fish/
├── dunst/       → ~/.config/dunst/
├── starship/    → ~/.config/starship/
├── vicinae/     → ~/.config/vicinae/
├── nwg-dock/    → ~/.config/nwg-dock-hyprland/
├── spicetify/   → ~/.config/spicetify/
└── packages/    # package lists and update script (not stowed)
```

`install.sh` runs `stow` on the core packages and installs all packages from `packages/pacman.txt` and `packages/aur.txt`. `nwg-dock` and `spicetify` are not in the default stow run and must be stowed manually.

## Hyprland config (Lua)

The config was migrated from hyprlang to Lua. Entry point is `hypr/.config/hypr/hyprland.lua`, which loads modules from `conf/` in order:

```
monitor → autostart → cursor → environments → input →
general → decoration → animations → layouts → gestures →
misc → windowrules → binds → host
```

`conf/host.lua` contains laptop-specific overrides (eDP-1 monitor, Swiss keyboard layout, touchpad sensitivity). Edit this file for machine-specific changes rather than the shared modules.

Key Lua API used:
- `hl.config({...})` — set Hyprland config variables
- `hl.bind(...)` — keybindings
- `hl.gesture({...})` — touchpad gestures
- `hl.on("hyprland.start", fn)` — autostart
- `hl.exec_cmd(...)` — run a command

## Waybar

Config is in `waybar/.config/waybar/`. The bar uses three floating pill groups:
- **Left** (`group/left`): launcher + workspaces + mpris
- **Center**: clock
- **Right** (`group/right`): cpu + memory + pulseaudio + network + bluetooth + battery + tray

Colors come from `colors/colors.css` (symlinked to `colors.dark.css` or `colors.light.css`). After editing config or CSS, restart waybar with `pkill waybar; waybar &`.

## Fish functions

Custom functions live in `fish/.config/fish/functions/`. Notable ones:

| Function | Purpose |
|----------|---------|
| `dotsync` | Commit + push dotfiles with auto hostname-tagged message |
| `hconf [module]` | Quick-edit a hyprland conf module in nano |
| `npr` | Interactive new project (Swisscom / business / education paths) |
| `npu` | Create and push a new public GitHub repo |
| `update_all` | System-wide update (pacman → AUR → pnpm → dotsync) |

Environment-specific fish config goes in `fish/.config/fish/conf.d/arch.fish` or `conf.d/wsl.fish`.

## Multi-machine workflow

`dotsync` tags commits with the hostname (`uname -n`), enabling multiple machines to push to the same repo. Machine-specific Hyprland settings belong in `conf/host.lua` only — shared modules should stay generic.
