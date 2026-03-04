# 1. wsl specific paths
set -gx BIZ_PATH $HOME/projects/03_business
set -gx EDU_PATH $HOME/projects/02_education
set -gx PLAY_PATH $HOME/projects/04_playground

# 2. navigation abbreviations
abbr -a cdbiz "cd $BIZ_PATH"
abbr -a cdedu "cd $EDU_PATH"
abbr -a cdplay "cd $PLAY_PATH"

# Swisscom WSL Setup ---
if test -f ~/.wsl4sc
    bash -c "source ~/.wsl4sc >/dev/null; env" | grep -E '^[A-Za-z0-9_]+=.*$' | while read -l line
        set name value (string split -m 2 '=' $line)
        set -gx $name $value
    end
end
