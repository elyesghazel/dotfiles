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

echo "Done!"
