# 2. kill process on port
function kport
    if test (count $argv) -eq 0
        echo "usage: kp <port>"
        return 1
    end

    set -l pids (lsof -ti tcp:$argv[1])

    if test -z "$pids"
        echo "no process on port $argv[1]"
        return 0
    end

    for pid in $pids
        kill -9 $pid
    end
end