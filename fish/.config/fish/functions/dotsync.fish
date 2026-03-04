# 1. sync everything to github
function dotsync
    set -l dotpath "$HOME/dotfiles"

    # update package lists first
    bash $dotpath/update_pkg.sh

    cd $dotpath
    git add .

    # get current timestamp
    set -l current_time (date "+%Y-%m-%d %H:%M")

    # detect system for commit message
    if set -q OS_KIND
        set -l system_name (string upper $OS_KIND)
        git commit -m "auto-sync [$system_name]: $current_time"
    else
        # fallback if OS_KIND is not set
        git commit -m "auto-sync: $current_time"
    end

    git push origin main

    echo "Everything synced to GitHub!"
end
