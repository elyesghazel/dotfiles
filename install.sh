#!/bin/bash

# 1. Pacman Pakete installieren
echo "Installing official pacman packages"
sudo pacman -S --needed - < ~/dotfiles/pacman_pkgs.txt

# 2. Insttall yay if not done yet.
if ! command -v yay &> /dev/null; then
    echo "Yay binary missing -> installing it..."
    sudo pacman -S --needed git base-devel
    git clone https://aur.archlinux.org/yay.git /tmp/yay
    cd /tmp/yay && makepkg -si --noconfirm
    cd ~/dotfiles
fi

# 3. Install AUR packages
echo "Installing AUR packages.."
yay -S --needed - < ~/dotfiles/aur_pkgs.txt

# 4. Linking
echo "Linking with stow"
stow fish kitty hypr waybar dunst swww

echo "Installation finished!"