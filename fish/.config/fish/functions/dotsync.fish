function dotsync --description "Commit + push dotfiles using Conventional Commits"
    set -l dotpath "$HOME/dotfiles"
    set -l host (uname -n)

    bash $dotpath/packages/update.sh update

    # settings.json is copy-synced, not stowed — Claude Code rewrites it
    # atomically and would clobber a symlink. Pull the live version back in.
    if test -f $HOME/.claude/settings.json
        cp $HOME/.claude/settings.json $dotpath/claude/.claude/settings.json
    end

    cd $dotpath

    if git diff --quiet; and git diff --cached --quiet; and test -z (git ls-files --others --exclude-standard | head -1)
        echo "Nothing to sync."
        return 0
    end

    git add .

    # Pass a Conventional Commits subject: dotsync "feat(hypr): add gesture binds"
    # With no argument this falls back to a plain sync commit.
    if set -q argv[1]
        set -l msg "$argv"
        if not string match -qr '^(feat|fix|refactor|perf|docs|style|test|build|ci|chore|revert)(\([a-z0-9._-]+\))?!?: .+' -- $msg
            echo "warning: \"$msg\" is not a Conventional Commits subject."
            echo "         expected e.g. feat(hypr): add gesture binds"
            read -l -P "commit anyway? [y/N] " confirm
            if not string match -qi y -- $confirm
                echo "Aborted."
                return 1
            end
        end
        git commit -m "$msg"
    else
        git commit -m "chore(sync): update dotfiles from $host"
    end

    git push origin main
    echo "Everything synced to GitHub!"
end
