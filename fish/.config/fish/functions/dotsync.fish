# 1. sync everything to github
function dotsync
    set -l dotpath "$HOME/dotfiles"
    
    # update package lists first
    bash $dotpath/update_pkg.sh
    
    cd $dotpath
    git add .
    
    # commit with timestamp
    set -l current_time (date "+%Y-%m-%d %H:%M")
    git commit -m "auto-sync: $current_time"
    
    git push origin main
    
    echo "Everything synced to GitHub!"
end