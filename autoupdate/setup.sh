#!/bin/bash
# Install the unattended-upgrade timer. Run as root: sudo ./autoupdate/setup.sh
# Files are copied, not stowed - root runs them, so they must not be
# symlinks into a user-writable home directory.
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "run with sudo" >&2; exit 1; }
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /  # pkexec starts in /root; runuser fish below warns it cannot read it

# Keep modules of the running kernel usable after an unattended kernel upgrade,
# and cap the package cache that daily upgrades would otherwise grow forever.
# pacman -T needs no lock, so re-running setup while an upgrade is going is safe.
pacman -T kernel-modules-hook pacman-contrib >/dev/null ||
    pacman -S --needed --noconfirm kernel-modules-hook pacman-contrib

id aurbuilder &>/dev/null || useradd --system --create-home \
    --home-dir /var/lib/aurbuilder --shell /usr/bin/nologin aurbuilder

visudo -cf "$DIR/sudoers"
install -Dm440 "$DIR/sudoers"           /etc/sudoers.d/autoupdate
install -Dm755 "$DIR/autoupdate"        /usr/local/bin/autoupdate
install -Dm644 "$DIR/autoupdate.service" /etc/systemd/system/autoupdate.service
install -Dm644 "$DIR/autoupdate.timer"   /etc/systemd/system/autoupdate.timer
install -Dm755 "$DIR/autoupdate-notify"         /usr/local/bin/autoupdate-notify
install -Dm644 "$DIR/autoupdate-notify.service" /etc/systemd/system/autoupdate-notify.service

# Failure alerts reuse the ntfy creds of the `clip` fish function. Copied into a
# root-only file because the service can't read (and shouldn't depend on) ~/.
ADMIN="${SUDO_USER:-$(id -nu "${PKEXEC_UID:-0}")}"
SECRETS="$(getent passwd "$ADMIN" | cut -d: -f6)/.claude/secrets.fish"
install -dm700 /etc/autoupdate
if [ -f "$SECRETS" ] && runuser -u "$ADMIN" -- fish -c \
        "source $SECRETS; set -q NTFY_URL NTFY_TOPIC NTFY_TOKEN" 2>/dev/null; then
    ( umask 077
      runuser -u "$ADMIN" -- fish -c "source $SECRETS
          printf 'NTFY_URL=%s\nNTFY_TOPIC=%s\nNTFY_TOKEN=%s\n' \$NTFY_URL \$NTFY_TOPIC \$NTFY_TOKEN" \
          > /etc/autoupdate/ntfy.env )
    echo "ntfy failure alerts: on (topic from $SECRETS)"
else
    echo "ntfy failure alerts: off - set NTFY_URL/NTFY_TOPIC/NTFY_TOKEN in $SECRETS and re-run"
fi

systemctl daemon-reload
systemctl enable --now autoupdate.timer paccache.timer linux-modules-cleanup.service
systemctl list-timers autoupdate.timer
