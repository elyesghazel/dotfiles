# What Runs On This Machine

> Inventory of services, timers, and autostart programs on the Arch + Hyprland box.
> Regenerate the live state with `dotfiles/packages/update.sh services` (see bottom).
> Last hand-updated: 2026-06-14.

---

## systemd — system services (enabled)

| Unit | Purpose |
| ---- | ------- |
| `NetworkManager.service` | Networking (+ `NetworkManager-dispatcher`, `NetworkManager-wait-online`) |
| `bluetooth.service` | Bluetooth stack |
| `cups.service` | Printing (also `cups.socket`) |
| `docker.service` | Docker daemon |
| `sddm.service` | Display manager / login screen |
| `systemd-timesyncd.service` | NTP time sync |
| `getty@.service` | Virtual terminals |

## systemd — system timers

| Timer | Runs |
| ----- | ---- |
| `fstrim.timer` | Weekly SSD TRIM |
| `shadow.timer` | Daily passwd/shadow backup |
| `systemd-tmpfiles-clean.timer` | Daily temp cleanup |
| `archlinux-keyring-wkd-sync.timer` | Keyring refresh |

## systemd — sockets

`cups.socket`, `systemd-userdbd.socket`

---

## systemd — user services (enabled, `systemctl --user`)

| Unit | Purpose |
| ---- | ------- |
| `pipewire.socket` / `pipewire-pulse.socket` | Audio server |
| `wireplumber.service` | PipeWire session manager |
| `p11-kit-server.socket` | PKCS#11 / smartcard proxy |
| `xdg-user-dirs.service` | Populates `~/.config/user-dirs.dirs` |
| `claude-cowork.service` | Claude Code cowork helper |

---

## Hyprland autostart (`hypr/.config/hypr/hyprland.lua` → `exec_cmd`)

| Command | Purpose |
| ------- | ------- |
| `waybar` | Status bar |
| `dunst` | Notification daemon |
| `/usr/lib/polkit-kde-authentication-agent-1` | Polkit auth prompts |
| `vicinae server` | Launcher/clipboard daemon |
| `nm-applet` | Network tray applet |
| `awww-daemon` + `awww img ~/wallpapers/DT2.jpg` | Wallpaper daemon |
| `hypridle` | Idle/lock management |
| `quickshell -p ~/apps/qs-hyprview` | Hyprview overlay (smartgrid/expose) |
| `wl-paste --watch cliphist store` (text + image) | Clipboard history |
| `~/.config/ml4w-hyprland-settings/hyprctl.sh` | ML4W runtime settings |

ℹ️ **Vicinae protobuf note (resolved 2026-06-14):** `vicinae-git` used to be linked
against `libprotobuf.so.33` while the system shipped protobuf 35, so the launch line
preloaded old libs from `/opt/vicinae-libs`. After rebuilding (`yay -S vicinae-git`)
the binary links the current protobuf, the `LD_LIBRARY_PATH` prefix was dropped, and
the `/opt/vicinae-libs` bundle was removed. If a future protobuf bump breaks vicinae
again, just `yay -S vicinae-git` to rebuild.

---

## XDG autostart (`~/.config/autostart/*.desktop`)

| Entry | Purpose |
| ----- | ------- |
| `discord.desktop` / `vesktop.desktop` | Discord (Vesktop client) |
| `spotify.desktop` | Spotify |
| `Flameshot.desktop` | Screenshot tool tray |
| `OpenRGB.desktop` | RGB lighting control |
| `RQuickShare.desktop` | Nearby Share for Linux |
| `jetbrains-toolbox.desktop` | JetBrains Toolbox |
| `lunarclient.desktop` | Lunar Client (Minecraft) |
| ~~`vicinae.desktop`~~ | **Disabled** — duplicate of the Hyprland launch; was crash-looping a failed systemd user unit. |

---

## Quick commands

```bash
# Live system state
systemctl list-unit-files --state=enabled              # enabled system units
systemctl --user list-unit-files --state=enabled       # enabled user units
systemctl list-timers                                  # active timers
systemctl --failed ; systemctl --user --failed         # anything broken
ls ~/.config/autostart/                                # XDG autostart entries
```
