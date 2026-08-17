#!/bin/bash

DOTFILES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing official packages"
sudo pacman -S --needed - < "$DOTFILES/packages/pacman.txt"

echo "==> Checking for yay"
if ! command -v yay &> /dev/null; then
    echo "yay not found — installing..."
    sudo pacman -S --needed git base-devel
    git clone https://aur.archlinux.org/yay.git /tmp/yay
    cd /tmp/yay && makepkg -si --noconfirm
    cd "$DOTFILES"
fi

echo "==> Installing AUR packages"
yay -S --needed - < "$DOTFILES/packages/aur.txt"

echo "==> Checking for Claude Code"
if ! command -v claude &> /dev/null; then
    echo "claude not found — installing..."
    if command -v npm &> /dev/null; then
        npm install -g @anthropic-ai/claude-code
    else
        echo "npm not found — installing nodejs first"
        sudo pacman -S --needed nodejs npm
        npm install -g @anthropic-ai/claude-code
    fi
fi

echo "==> Linking configs with stow"
cd "$DOTFILES"
stow fish kitty hypr waybar dunst starship vicinae claude

echo "==> Installing Claude settings.json"
# Not stowed: Claude Code rewrites this file atomically, which would replace a
# symlink with a regular file. Copied instead; dotsync copies changes back.
mkdir -p "$HOME/.claude"
if [ -f "$HOME/.claude/settings.json" ] && \
   ! diff -q "$DOTFILES/claude/.claude/settings.json" "$HOME/.claude/settings.json" >/dev/null; then
    cp "$HOME/.claude/settings.json" "$HOME/.claude/settings.json.bak.$(date +%Y%m%d-%H%M%S)"
    echo "    existing settings.json differed — backed up"
fi
cp "$DOTFILES/claude/.claude/settings.json" "$HOME/.claude/settings.json"

echo "==> Registering Claude MCP servers"
# MCP servers live in ~/.claude.json alongside oauth tokens and machine state,
# so they are rebuilt from the tracked bootstrap script rather than synced.
if [ -f "$HOME/.claude/secrets.fish" ]; then
    fish "$HOME/.claude/bin/mcp-bootstrap.fish"
else
    echo "    skipped — no ~/.claude/secrets.fish yet."
    echo "    cp ~/.claude/secrets.fish.example ~/.claude/secrets.fish, fill it in,"
    echo "    then run: fish ~/.claude/bin/mcp-bootstrap.fish"
fi

echo "Done!"
