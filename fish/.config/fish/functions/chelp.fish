# Custom help command for fish shell
function chelp
    set_color blue
    echo "═══════════════════════════════════════════"
    set_color yellow
    echo "  Custom Shell Help"
    set_color blue
    echo "═══════════════════════════════════════════"
    set_color normal

    if test (count $argv) -eq 0
        # Main help menu
        echo ""
        set_color green
        echo "📖 Available Help Topics:"
        set_color normal
        echo "  chelp functions  - View all custom fish functions"
        echo "  chelp keybinds   - View Hyprland keybindings"
        echo ""
        set_color green
        echo "🔧 Quick Command List:"
        set_color normal
        echo "  dotsync      - Sync dotfiles to GitHub"
        echo "  kport <port> - Kill process on specified port"
        echo "  hconf [file] - Edit Hyprland configs"
        echo "  npr          - Create new project (interactive)"
        echo "  npu [name]   - Create new GitHub repo"
        echo "  t <time>     - Start background timer"
        echo "  update_all   - Full system update"
        echo ""
    else if test "$argv[1]" = "functions"
        _help_functions
    else if test "$argv[1]" = "keybinds"
        _help_keybinds
    else
        set_color red
        echo "Unknown help topic: $argv[1]"
        set_color normal
        echo "Try: chelp functions, chelp keybinds"
    end
end

# Detailed function descriptions
function _help_functions
    echo ""
    set_color cyan
    echo "📦 Custom Fish Functions:"
    set_color normal
    echo ""
    
    set_color yellow
    echo "1. dotsync"
    set_color normal
    echo "   Description: Syncs dotfiles to GitHub"
    echo "   Usage:       dotsync"
    echo "   Details:     Updates package lists, commits with timestamp, and pushes to main"
    echo ""
    
    set_color yellow
    echo "2. kport"
    set_color normal
    echo "   Description: Kills process running on specified port"
    echo "   Usage:       kport <port>"
    echo "   Example:     kport 3000"
    echo ""
    
    set_color yellow
    echo "3. hconf"
    set_color normal
    echo "   Description: Edit Hyprland configuration files"
    echo "   Usage:       hconf [filename]"
    echo "   Example:     hconf binds    # opens binds.conf"
    echo "                hconf          # opens main hyprland.conf"
    echo ""
    
    set_color yellow
    echo "4. npr"
    set_color normal
    echo "   Description: Create new project (interactive)"
    echo "   Usage:       npr"
    echo "   Details:     Interactive menu to create projects in categorized folders"
    echo ""
    
    set_color yellow
    echo "5. npu"
    set_color normal
    echo "   Description: Create new GitHub repository"
    echo "   Usage:       npu [name] [-p]"
    echo "   Example:     npu my-repo      # creates public repo"
    echo "                npu my-repo -p   # creates private repo"
    echo ""
    
    set_color yellow
    echo "6. t (timer)"
    set_color normal
    echo "   Description: Start background timer with notification"
    echo "   Usage:       t <duration>"
    echo "   Example:     t 5m    # 5 minute timer"
    echo "                t 30s   # 30 second timer"
    echo ""
    
    set_color yellow
    echo "7. update_all"
    set_color normal
    echo "   Description: Full system update (pacman, aur, pnpm, dotfiles)"
    echo "   Usage:       update_all"
    echo "   Details:     Updates all packages and syncs dotfiles to GitHub"
    echo ""
end

# Hyprland keybinds help
function _help_keybinds
    echo ""
    set_color cyan
    echo "⌨️  Hyprland Keybindings (SUPER = Mod Key):"
    set_color normal
    echo ""
    
    set_color magenta
    echo "▸ Applications"
    set_color normal
    echo "  SUPER + RETURN        → Terminal (kitty)"
    echo "  SUPER + E             → File Manager (thunar)"
    echo "  SUPER + B             → Browser (zen-browser)"
    echo "  SUPER + V             → Clipboard History"
    echo "  ALT + SPACE           → App Launcher (vicinae)"
    echo "  SUPER + ALT + W       → Random Wallpaper"
    echo ""
    
    set_color magenta
    echo "▸ Session Management"
    set_color normal
    echo "  SUPER + Q / C         → Kill Active Window"
    echo "  SUPER + M             → Exit Hyprland"
    echo "  SUPER + L             → Lock Screen"
    echo "  SUPER + BACKSPACE     → Logout Menu (wlogout)"
    echo ""
    
    set_color magenta
    echo "▸ Window States"
    set_color normal
    echo "  SUPER + F             → Fullscreen"
    echo "  SUPER + SPACE         → Toggle Floating"
    echo "  SUPER + P             → Pseudo Tiling"
    echo "  SUPER + J             → Toggle Split"
    echo ""
    
    set_color magenta
    echo "▸ Focus & Movement"
    set_color normal
    echo "  SUPER + Arrow Keys    → Move Focus"
    echo "  SUPER + SHIFT + Arrow → Move Window"
    echo ""
    
    set_color magenta
    echo "▸ Workspaces"
    set_color normal
    echo "  SUPER + [1-9,0]       → Switch to Workspace"
    echo "  SUPER + SHIFT + [1-9] → Move Window to Workspace"
    echo "  SUPER + H             → Move to Special Workspace"
    echo "  SUPER + SHIFT + H     → Toggle Special Workspace"
    echo ""
    
    set_color magenta
    echo "▸ Media Controls"
    set_color normal
    echo "  XF86AudioRaiseVolume  → Volume Up"
    echo "  XF86AudioLowerVolume  → Volume Down"
    echo "  XF86AudioMute         → Toggle Mute"
    echo ""
    
    set_color magenta
    echo "▸ Screenshots"
    set_color normal
    echo "  SUPER + SHIFT + S     → Selection to Clipboard"
    echo "  SUPER + S             → Full Screen to Clipboard"
    echo "  SUPER + ALT + S       → Selection to File"
    echo ""
    
    set_color magenta
    echo "▸ Mouse"
    set_color normal
    echo "  SUPER + Left Click    → Move Window"
    echo "  SUPER + Right Click   → Resize Window"
    echo ""
end

# Completions for chelp command
complete -c chelp -a "functions keybinds" -d "Help topics"
