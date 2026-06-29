-- https://wiki.hypr.land/Configuring/Basics/Autostart/
hl.on("hyprland.start", function()
    -- core services
    hl.exec_cmd("waybar")
    hl.exec_cmd("dunst")
    hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
    hl.exec_cmd("vicinae server")
    hl.exec_cmd("nm-applet")
    -- wallpaper & display
    hl.exec_cmd("awww-daemon")
    hl.exec_cmd("hyprctl dispatch focusmonitor DP-2")
    hl.exec_cmd("awww img ~/wallpapers/DT2.jpg")

    -- external settings
    hl.exec_cmd("~/.config/ml4w-hyprland-settings/hyprctl.sh")

    -- clipboard history
    hl.exec_cmd("wl-paste --type text --watch cliphist store")
    hl.exec_cmd("wl-paste --type image --watch cliphist store")

    hl.exec_cmd("hypridle")
    hl.exec_cmd("quickshell -p /home/elyes/apps/qs-hyprview")
    hl.exec_cmd("sudo rc-service claude-cowork start")
end)
