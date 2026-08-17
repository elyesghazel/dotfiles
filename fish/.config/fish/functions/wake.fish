# ~/.config/fish/functions/wake.fish
# Purpose: Wake a home machine over Wake-on-LAN by bouncing a magic packet off the
#          always-on Raspberry Pi, which sits on the home LAN.
# Usage:   wake [host]     (default: arch)
#          wake --status   just report whether the target is up
#
# Why via the Pi: a WoL magic packet is a layer-2 broadcast, so it must originate
# INSIDE the home LAN. The VPS cannot send one. Going through the Pi every time
# keeps one code path that works from home and from outside alike.
#
# Setup: see docs/wake-on-lan.md

function _wake_online --argument-names host --description 'Is a tailnet host up?'
    set -l line (tailscale status 2>/dev/null | string match -r ".*\s$host\s.*")
    test -z "$line"; and return 1
    string match -q '*offline*' -- "$line"; and return 1
    return 0
end

function wake --description 'Wake a home machine over Wake-on-LAN via the Pi'
    # ---- config ----------------------------------------------------------
    # Tailscale hostname of the always-on Pi on the home LAN.
    set -l pi pi-home
    # target -> tailscale hostname -> MAC of its WIRED nic.
    # Get the MAC on the target with:  ip -br link
    set -l ts_host elyes-arch
    set -l mac "FILL:ME:IN:00:00:00"
    # ----------------------------------------------------------------------

    if contains -- --status $argv
        if _wake_online $ts_host
            echo "$ts_host is up."
        else
            echo "$ts_host is down."
        end
        return 0
    end

    if _wake_online $ts_host
        echo "$ts_host is already up."
        return 0
    end

    if string match -q '*FILL:ME:IN*' -- $mac
        echo "wake: set the MAC of $ts_host in "(status filename)
        return 1
    end

    if not _wake_online $pi
        echo "wake: the Pi ($pi) is not on the tailnet — cannot send the packet."
        return 1
    end

    # python3 ships with Raspberry Pi OS, so nothing needs installing there.
    # Single-quoted for the remote shell; the body deliberately uses no single quotes.
    set -l py 'import socket,sys;m=sys.argv[1].replace(":","").replace("-","");p=b"\xff"*6+bytes.fromhex(m)*16;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1);[s.sendto(p,("255.255.255.255",n)) for n in (7,9)];print("magic packet sent")'

    echo "Waking $ts_host ($mac) via $pi ..."
    if not ssh $pi "python3 -c '$py' '$mac'"
        echo "wake: failed to send the packet"
        return 1
    end

    echo -n "Waiting for $ts_host to join the tailnet"
    for i in (seq 60)
        if _wake_online $ts_host
            echo
            echo "$ts_host is up."
            return 0
        end
        echo -n "."
        sleep 2
    end

    echo
    echo "wake: $ts_host did not come up within 2 min."
    echo "      Check BIOS ErP/Deep-Sleep is DISABLED, that ethtool reports Wake-on: g,"
    echo "      and that it is on wired ethernet. See docs/wake-on-lan.md"
    return 1
end
