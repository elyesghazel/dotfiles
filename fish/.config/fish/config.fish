# ═══════════════════════════════════════════════════════════════════════════
# ELYES - FISH SHELL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

set -g fish_greeting ""

# ─────────────────────────────────────────────────────────────────────────
# ENVIRONMENT & CORE PATHS
# ─────────────────────────────────────────────────────────────────────────

if test (uname) = "Linux"; and not test -n "$WSL_DISTRO_NAME"
    set -gx EDITOR "code --wait"
    set -gx BIZ_PATH $HOME/projects/03_business
    set -gx EDU_PATH $HOME/projects/02_education
    set -gx PLAY_PATH $HOME/projects/04_playground
    
    fish_add_path $HOME/.platformio/penv/bin
else
    # WSL / WINDOWS
    set -gx EDITOR "code --wait"
    set -gx BIZ_PATH $HOME/projects/03_business
    set -gx EDU_PATH $HOME/projects/02_education
    set -gx PLAY_PATH $HOME/projects/04_playground
end

# ─────────────────────────────────────────────────────────────────────────
# ABBREVIATIONS
# ─────────────────────────────────────────────────────────────────────────

# Navigation
abbr -a cdbiz "cd $BIZ_PATH"
abbr -a cdedu "cd $EDU_PATH"
abbr -a cdplay "cd $PLAY_PATH"

# Development & Git
abbr -a g "git"
abbr -a gs "git status"
abbr -a gc "git commit -m"
abbr -a gp "git push"
abbr -a prd "pnpm run dev"
abbr -a pni "pnpm install"
abbr -a cd "z"
# System Config
abbr -a fconf "nano ~/.config/fish/config.fish"
abbr -a vconf "nano ~/.config/vicinae/config.json"

# ─────────────────────────────────────────────────────────────────────────
# FUNCTION: Create New Project (npr)
# ─────────────────────────────────────────────────────────────────────────
function npr
    echo "Select project category:"
    echo "1) Swisscom"
    echo "2) Business / Private"
    echo "3) Education / School"
    read -l choice

    set -l base_path ""
    switch $choice
        case 1
            set base_path $HOME/projects/01_swisscom
        case 2
            set base_path $BIZ_PATH
        case 3
            set base_path $EDU_PATH
        case '*'
            echo "Error: Invalid selection."
            return 1
    end

    echo "Enter project name:"
    read -l project_name

    if test -z "$project_name"
        echo "Error: Project name cannot be empty."
        return 1
    end

    set -l final_path "$base_path/$project_name"

    mkdir -p $final_path
    cd $final_path
    git init -b main
    echo "# $project_name" > README.md
    
    echo "Status: Project initialized at $final_path"
    code .
end

# ─────────────────────────────────────────────────────────────────────────
# FUNCTION: GitHub Public Repo Creator (npu)
# ─────────────────────────────────────────────────────────────────────────
function npu
    set -l repo_name ""
    set -l visibility "--public"
    set -l playground_path "$HOME/projects/04_playground"

    # 1. Parse Arguments
    for arg in $argv
        if test "$arg" = "-p"
            set visibility "--private"
        else
            set repo_name $arg
        end
    end

    # 2. Determine Path & Name
    if test -n "$repo_name"
        set -l final_path "$playground_path/$repo_name"
        mkdir -p $final_path
        cd $final_path
    else
        set repo_name (basename (pwd))
        if test (pwd) = "$HOME"
            echo "Error: Cannot initialize repository in HOME directory."
            return 1
        end
    end

    # 3. Git Initialization
    if not test -d .git
        git init -b main
    end

    if not test -f README.md
        echo "# $repo_name" > README.md
    end

    # 4. Commit and Sync
    git add .
    git commit -m "Initial commit" 2>/dev/null

    if command -sq gh
        echo "Status: Syncing $repo_name to GitHub ($visibility)..."
        if gh repo create $repo_name $visibility --source=. --remote=origin --push 2>/dev/null
            echo "✅ Success: $visibility repository created."
        else
            echo "Notice: Repository might already exist. Attempting push..."
            git push -u origin (git branch --show-current)
        end
    else
        echo "Error: GitHub CLI (gh) not found."
        return 1
    end

    code .
end

function kp
    if test (count $argv) -eq 0
        echo "Usage: kp <port>"
        return 1
    end

    set port $argv[1]
    set pids (lsof -ti tcp:$port)

    if test -z "$pids"
        echo "No process found using port $port."
        return 0
    end

    for pid in $pids
        echo "Killing process $pid using port $port..."
        kill -9 $pid
    end
end


# ________________________________________________________________________
# FUNCTION: Background Timer (t)
# ─────────────────────────────────────────────────────────────────────────
function t
    # Prüfen, ob wir auf Linux mit GUI sind
    if type -q notify-send
        nohup bash -c "sleep $argv[1] && notify-send 'Timer Expired' 'Duration: $argv[1]' && paplay /usr/share/sounds/freedesktop/stereo/complete.oga" >/dev/null 2>&1 &
        echo "Timer started for $argv[1] (Linux Desktop Mode)."
    else
        # Fallback für WSL
        nohup bash -c "sleep $argv[1] && echo -e '\a'" >/dev/null 2>&1 &
        echo "Timer started for $argv[1] (Terminal Bell)."
    end
end

zoxide init fish | source
