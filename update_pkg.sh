#!/bin/bash
# 1. update package lists
pacman -Qqen > ~/dotfiles/pacman_pkgs.txt
pacman -Qqem > ~/dotfiles/aur_pkgs.txt

echo "Package lists updated."