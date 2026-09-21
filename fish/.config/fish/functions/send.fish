# ~/.config/fish/functions/send.fish
# Purpose: Push files to another device on the tailnet with Taildrop. On-demand
#          only - nothing syncs, nothing runs in the background.
# Usage:   send <host> <files...>       push files          (send elyes-iphone a.pdf b.jpg)
#          <cmd> | send <host> [name]   push stdin as a file (wl-paste | send pixel-9 note.txt)
#          send --get [dir]             pull received files out of the inbox (default ~/tailscale-files)
#          send --targets               list devices that can receive right now
#
# Why --get: phones pop received files up in the Tailscale app, Linux does not -
# they sit in a hidden inbox until `tailscale file get` moves them out. The
# taildrop-inbox user service (systemd package) does that continuously.
#
# Setup (once per Linux box, so no sudo is needed):  sudo tailscale set --operator=$USER
# Text you want to PASTE on the phone is better sent with `clip` (ntfy), not here.

function send --description 'Taildrop files to a tailnet device'
    switch "$argv[1]"
        case --targets -t
            tailscale file cp --targets
            return
        case --get -g
            set -l dir ~/tailscale-files
            test -n "$argv[2]"; and set dir $argv[2]
            tailscale file get --conflict=rename $dir
            return
        case '' -h --help
            echo "usage: send <host> <files...> | <cmd> | send <host> [name] | send --get [dir] | send --targets"
            return 1
    end

    set -l host $argv[1]

    if not isatty stdin
        # Piped input: Taildrop needs a filename for stdin.
        set -l name (date +%Y%m%d-%H%M%S).txt
        test -n "$argv[2]"; and set name $argv[2]
        tailscale file cp --name $name - $host:
        return
    end

    if test (count $argv) -lt 2
        echo "send: nothing to send (pass files or pipe stdin)" >&2
        return 1
    end
    tailscale file cp $argv[2..] $host:
end
