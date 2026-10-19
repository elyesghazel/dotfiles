# ~/.config/fish/functions/sleep-pc.fish
# Purpose: Power off the home PC remotely — the counterpart to `wake`.
# Usage:   sleep-pc
#
# Why via Hyprland: polkit refuses `systemctl poweroff` from an SSH session (it is not
# the active local session). Asking Hyprland to exec it runs the command inside the
# seat0 session, which polkit allows without a password.

function sleep-pc --description 'Power off the home PC over SSH via its Hyprland session'
    set -l host arch
    set -l ts_host elyes-arch

    if not tailscale status 2>/dev/null | string match -qr "\s$ts_host\s(?!.*offline)"
        echo "$ts_host is already down."
        return 0
    end

    # Hyprland uses the Lua config, hence hl.dsp.exec_cmd rather than `dispatch exec`.
    # Falls back to a plain poweroff when nobody is logged in to Hyprland.
    set -l remote 'rt=/run/user/$(id -u); sig=$(ls $rt/hypr/ 2>/dev/null | head -1)
if [ -n "$sig" ]; then
    XDG_RUNTIME_DIR=$rt HYPRLAND_INSTANCE_SIGNATURE=$sig hyprctl dispatch '"'"'hl.dsp.exec_cmd("systemctl poweroff")'"'"'
else
    systemctl poweroff
fi'

    echo "Powering off $ts_host ..."
    if not printf '%s\n' $remote | ssh -o ConnectTimeout=10 $host bash -s
        echo "sleep-pc: could not send the poweroff"
        return 1
    end

    echo -n "Waiting for $ts_host to leave the tailnet"
    for i in (seq 30)
        if tailscale status 2>/dev/null | string match -qr "\s$ts_host\s.*offline"
            echo
            echo "$ts_host is off."
            return 0
        end
        echo -n "."
        sleep 3
    end

    echo
    echo "sleep-pc: $ts_host still shows online after 90s — Tailscale can lag; check with: wake --status"
    return 1
end
