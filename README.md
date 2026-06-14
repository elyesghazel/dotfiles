# ELYES' DOTFILES

![Arch Linux](https://img.shields.io/badge/OS-Arch%20Linux-blue?style=for-the-badge&logo=arch-linux)
![WM](https://img.shields.io/badge/WM-Hyprland-89b4fa?style=for-the-badge&logo=hyprland)
![Shell](https://img.shields.io/badge/Shell-Fish-orange?style=for-the-badge&logo=fish)

![Screenshot](assets/image.png)

Personal configuration files for Arch Linux (Hyprland) and WSL (CLI).

---

## Structure

```
dotfiles/
├── RUNNING.md          inventory of services/timers/autostart on this machine
├── packages/
│   ├── pacman.txt      official Arch packages
│   ├── aur.txt         AUR packages
│   └── update.sh       export / list / diff packages, dump services
├── fish/               shell — functions, completions, conf.d
├── hypr/               Hyprland WM (Lua config, modular conf/)
├── waybar/             status bar
├── dunst/              notification daemon
├── kitty/              terminal emulator
├── starship/           shell prompt
├── vicinae/            launcher & clipboard
└── spicetify/          Spotify theming
```

---

## Installation

> **Note:** Review configs before running — some paths (monitor names, home dirs) are hardcoded for my machine.

```bash
git clone https://github.com/elyesghazel/dotfiles.git ~/dotfiles
cd ~/dotfiles
chmod +x install.sh
./install.sh
```

This installs all packages from `packages/pacman.txt` and `packages/aur.txt`, then links configs via `stow`.

---

## Package Management

```bash
packages/update.sh update   # export installed packages → lists
packages/update.sh list     # show all packages in the lists
packages/update.sh diff     # compare system vs lists
```

---

## Keybinds

| Keybind             | Action                      |
| ------------------- | --------------------------- |
| `SUPER + RETURN`    | Open Kitty terminal         |
| `SUPER + TAB`       | Hyprview (smartgrid)        |
| `ALT + SPACE`       | Vicinae launcher            |
| `SUPER + S`         | Screenshot → clipboard      |
| `SUPER + SHIFT + S` | Screenshot (area selection) |
| `SUPER + ALT + W`   | Randomize wallpaper         |
| `SUPER + B`         | Zen Browser                 |
| `SUPER + V`         | Clipboard history           |
| `SUPER + L`         | Lock screen                 |

---

## Fish Functions

| Command    | Description                                      |
| ---------- | ------------------------------------------------ |
| `dotsync`  | Update package lists and push everything to git  |
| `hconf`    | Quick-edit Hyprland config files                 |
| `npr`      | Create a new local project                       |
| `npu`      | Create a new GitHub repo                         |
| `update_all` | Update pacman + AUR + other tools              |

---

## Theme

- **Font**: JetBrainsMono Nerd Font
- **Colors**: Catppuccin Mocha
- **Bar**: Waybar (pill style)
- **Notifications**: Dunst

---

_Maintained by Elyes_
