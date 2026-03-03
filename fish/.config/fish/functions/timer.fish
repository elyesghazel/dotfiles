# 3. background timer
function t
    if type -q notify-send
        nohup bash -c "sleep $argv[1] && notify-send 'Timer Expired' 'Duration: $argv[1]' && paplay /usr/share/sounds/freedesktop/stereo/complete.oga" >/dev/null 2>&1 &
        echo "timer started: $argv[1]"
    else
        nohup bash -c "sleep $argv[1] && echo -e '\a'" >/dev/null 2>&1 &
        echo "timer started (bell): $argv[1]"
    end
end