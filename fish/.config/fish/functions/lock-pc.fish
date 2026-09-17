function lock-pc --description "Lock this machine's Hyprland session with hyprlock (works over SSH)"
    if pgrep -x hyprlock >/dev/null
        echo "already locked"
        return 0
    end
    set -l rt /run/user/(id -u)
    set -l sig (ls $rt/hypr/ 2>/dev/null | head -1)
    set -l wl (ls $rt | grep -E '^wayland-[0-9]+$' | head -1)
    if test -z "$sig" -o -z "$wl"
        echo "no Hyprland session found"
        return 1
    end
    env XDG_RUNTIME_DIR=$rt WAYLAND_DISPLAY=$wl HYPRLAND_INSTANCE_SIGNATURE=$sig setsid -f hyprlock >/dev/null 2>&1
    sleep 2
    pgrep -x hyprlock >/dev/null && echo "locked" || echo "hyprlock did not start"
end
