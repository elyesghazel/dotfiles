#!/bin/bash

# 1. Update and install core tools
echo "updating system and installing core tools..."
sudo apt update && sudo apt install -y stow fish git build-essential

# 2. Install starship
if ! command -v starship &> /dev/null; then
    echo "installing starship..."
    curl -sS https://starship.rs/install.sh | sh -s -- -y
fi

# 3. Install zoxide
if ! command -v zoxide &> /dev/null; then
    echo "installing zoxide..."
    curl -sS https://zoxide.pw/install.sh | sh
fi

# 4. Linking (Only CLI tools)
echo "linking wsl dotfiles..."
cd ~/dotfiles
stow fish starship

# 5. Set fish as default shell
if [[ $SHELL != *"fish"* ]]; then
    echo "switching to fish shell..."
    chsh -s $(which fish)
fi

echo "WSL setup finished!"