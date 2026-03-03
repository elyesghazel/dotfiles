function update_all
    echo "Starting full system update..."

    # 1. Arch System Update (Pacman)
    echo "Updating Pacman packages..."
    sudo pacman -Syu --noconfirm

    # 2. AUR Update (Yay)
    if command -v yay > /dev/null
        echo "Updating AUR packages..."
        yay -Sua --noconfirm
    end

    # 3. PNPM Global Update
    if command -v pnpm > /dev/null
        echo "Updating global PNPM packages..."
        pnpm update -g
    end

    # 4. Dotfiles Sync
    echo "Syncing dotfiles to GitHub..."
    dotsync

    echo "✅ System is up to date and dotfiles are synced!"
end