function unlock-pc --description "Unlock the hyprlock screen of this session (run over SSH)"
    if pkill -USR1 -x hyprlock
        echo "hyprlock unlocked"
    else
        echo "hyprlock is not running"
    end
end
