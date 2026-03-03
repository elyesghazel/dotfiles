# 1. global settings
set -g fish_greeting ""
set -gx EDITOR "code --wait"

# 2. paths and systems
if test -n "$WSL_DISTRO_NAME"
    source ~/.config/fish/conf.d/wsl.fish
else
    source ~/.config/fish/conf.d/arch.fish
end

# 3. abbreviations
abbr -a g "git"
abbr -a gs "git status"
abbr -a gc "git commit -m"
abbr -a gp "git push"
abbr -a prd "pnpm run dev"
abbr -a pni "pnpm install"
abbr -a cd "z"
abbr -a fconf "nano ~/.config/fish/config.fish"
abbr -a vconf "nano ~/.config/vicinae/config.json"

# node & pnpm redirects
abbr -a n "pnpm"
abbr -a ni "pnpm install"
abbr -a nr "pnpm run"
abbr -a npm "pnpm"
abbr -a npx "pnpx"

# 4. interactive tools
zoxide init fish | source
starship init fish | source


# pnpm
set -gx PNPM_HOME "$HOME/.local/share/pnpm"
if not string match -q -- $PNPM_HOME $PATH
    set -gx PATH "$PNPM_HOME" $PATH
end
