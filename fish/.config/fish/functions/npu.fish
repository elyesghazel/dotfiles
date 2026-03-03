# 1. github public repo creator
function npu
    set -l repo_name ""
    set -l visibility "--public"
    set -l playground_path "$HOME/projects/04_playground"

    for arg in $argv
        if test "$arg" = "-p"
            set visibility "--private"
        else
            set repo_name $arg
        end
    end

    if test -n "$repo_name"
        set -l final_path "$playground_path/$repo_name"
        mkdir -p $final_path
        cd $final_path
    else
        set repo_name (basename (pwd))
    end

    if not test -d .git
        git init -b main
    end

    if not test -f README.md
        echo "# $repo_name" > README.md
    end

    git add .
    git commit -m "initial commit" 2>/dev/null

    if command -sq gh
        echo "syncing $repo_name to github ($visibility)..."
        gh repo create $repo_name $visibility --source=. --remote=origin --push
    end

    code .
end