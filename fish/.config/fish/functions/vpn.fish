# ~/.config/fish/functions/vpn.fish
# Purpose: bring the WireGuard tunnel up/down on demand, so wg-quick@wg0 does not
#          have to be enabled at boot.
# Usage:   vpn            toggle the tunnel
#          vpn up|on      start it
#          vpn down|off   stop it
#          vpn status     show whether it is up, and the peer handshake
#
# The interface defaults to wg0; override with $WG_IFACE or `vpn up <iface>`.

function vpn --description 'Toggle the WireGuard tunnel'
    set -l iface (set -q WG_IFACE; and echo $WG_IFACE; or echo wg0)
    set -l action

    for arg in $argv
        switch $arg
            case up on start
                set action up
            case down off stop
                set action down
            case status st
                set action status
            case '-h' '--help'
                echo "usage: vpn [up|down|status] [interface]   (default: $iface)"
                return 0
            case '*'
                set iface $arg
        end
    end

    set -l unit "wg-quick@$iface"

    if test -z "$action"
        if systemctl is-active -q $unit
            set action down
        else
            set action up
        end
    end

    switch $action
        case status
            if not systemctl is-active -q $unit
                echo "$iface is down."
                return 1
            end
            set -l addr (ip -br addr show $iface 2>/dev/null | string split -f3 ' ' -n)
            if test -n "$addr"
                echo "$iface is up — $addr"
            else
                echo "$iface is up."
            end
            # `wg show` needs root to read the keys. Only use it when sudo is
            # already unlocked (-n never prompts) so a status check stays free.
            sudo -n wg show $iface 2>/dev/null
            or echo "  peer details: sudo wg show $iface"
            return 0

        case up
            if systemctl is-active -q $unit
                echo "$iface is already up."
                return 0
            end
            sudo systemctl start $unit; or return 1
            echo "$iface is up."

        case down
            if not systemctl is-active -q $unit
                echo "$iface is already down."
                return 0
            end
            sudo systemctl stop $unit; or return 1
            echo "$iface is down."
    end
end
