# 1. sync everything to github
function dotsync
    set -l dotpath "$HOME/dotfiles"
    set -l current_time (date "+%Y-%m-%d %H:%M")
    set -l host (hostname)

    bash $dotpath/update_pkg.sh
    cd $dotpath
    git add .

    if set -q argv[1]
        git commit -m "auto-sync [$host]: $argv[1] – $current_time"
    else
        git commit -m "auto-sync [$host]: $current_time"
    end

    git push origin main
    echo "Everything synced to GitHub!"
end
