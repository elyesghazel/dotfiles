# 1. edit hyprland configs
function hconf
    if test (count $argv) -eq 0
        # no argument: open main config
        nano ~/.config/hypr/hyprland.conf
    else
        # with argument: open specific file in hypr folder
        nano ~/.config/hypr/conf/$argv[1].conf
    end
end
# completions for hconf function
complete -c hconf -a "binds rules settings"