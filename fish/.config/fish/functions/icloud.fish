# ~/.config/fish/functions/icloud.fish
# Purpose: Run the pyicloud CLI with its session kept in ~/.local/state/pyicloud
#          instead of /tmp/pyicloud, which is wiped on reboot and would force a
#          fresh password + 2FA login every boot.
# Usage:   icloud <anything>        icloud auth login --username you@icloud.com
#
# Why TMPDIR and not --session-dir: pyicloud only accepts --session-dir on leaf
# commands (icloud reminders list --session-dir ...), so injecting it means
# parsing argv. With no --session-dir it falls back to $TMPDIR/pyicloud/$USER.
#
# Install: uv tool install 'pyicloud[cli]' --with rich   (2.7.0 forgets rich)
# Needs "Access iCloud Data on the Web" on and Advanced Data Protection off.

function icloud --wraps icloud --description 'pyicloud CLI with a persistent session'
    mkdir -p ~/.local/state/pyicloud
    TMPDIR=$HOME/.local/state command icloud $argv
end
