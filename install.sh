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

echo "==> Linking configs with stow"
cd "$DOTFILES"
stow fish kitty hypr waybar dunst starship vicinae

echo "Done!"
