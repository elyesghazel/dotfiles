# 1. wsl specific paths
set -gx BIZ_PATH $HOME/projects/03_business
set -gx EDU_PATH $HOME/projects/02_education
set -gx PLAY_PATH $HOME/projects/04_playground

# 2. navigation abbreviations
abbr -a cdbiz "cd $BIZ_PATH"
abbr -a cdedu "cd $EDU_PATH"
abbr -a cdplay "cd $PLAY_PATH"

# Swisscom WSL Setup ---
if status is-interactive
    and test -t 0
    and not set -q FISH_WSL4SC_SHOWN
    set -g FISH_WSL4SC_SHOWN 1

    # Run ~/.wsl4sc *only* if terminal is interactive
    # and skip if it's called from VS Code or pipe:
    bash --login -i -c "source ~/.wsl4sc >/dev/null; env" | grep -E '^[A-Za-z0-9_]+=.*$' | while read -l line
        set name value (string split -m 2 '=' $line)
        set -gx $name $value
    end
end
