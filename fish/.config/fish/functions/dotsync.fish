function dotsync
    set -l dotpath "$HOME/dotfiles"
    set -l host (uname -n)
    set -l timestamp (date "+%Y-%m-%d %H:%M")

    bash $dotpath/packages/update.sh update
    cd $dotpath
    git add .

    if set -q argv[1]
        git commit -m "auto-sync [$host]: $argv[1] – $timestamp"
    else
        git commit -m "auto-sync [$host]: $timestamp"
    end

    git push origin main
    echo "Everything synced to GitHub!"
end
