#!/bin/bash

# Check if we are on Arch Linux
if command -v pacman &> /dev/null; then
    echo "Arch Linux detected. Updating package lists..."
    pacman -Qqen > ~/dotfiles/pacman_pkgs.txt
    pacman -Qqem > ~/dotfiles/aur_pkgs.txt
    echo "Package lists updated."
else
    echo "No pacman detected (WSL/Ubuntu). Skipping package export."
fi
