#!/bin/bash
# Install the unattended-upgrade timer. Run as root: sudo ./autoupdate/setup.sh
# Files are copied, not stowed - root runs them, so they must not be
# symlinks into a user-writable home directory.
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "run with sudo" >&2; exit 1; }
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Keep modules of the running kernel usable after an unattended kernel upgrade,
# and cap the package cache that daily upgrades would otherwise grow forever.
pacman -S --needed --noconfirm kernel-modules-hook pacman-contrib

id aurbuilder &>/dev/null || useradd --system --create-home \
    --home-dir /var/lib/aurbuilder --shell /usr/bin/nologin aurbuilder

visudo -cf "$DIR/sudoers"
install -Dm440 "$DIR/sudoers"           /etc/sudoers.d/autoupdate
install -Dm755 "$DIR/autoupdate"        /usr/local/bin/autoupdate
install -Dm644 "$DIR/autoupdate.service" /etc/systemd/system/autoupdate.service
install -Dm644 "$DIR/autoupdate.timer"   /etc/systemd/system/autoupdate.timer

systemctl daemon-reload
systemctl enable --now autoupdate.timer paccache.timer linux-modules-cleanup.service
systemctl list-timers autoupdate.timer
