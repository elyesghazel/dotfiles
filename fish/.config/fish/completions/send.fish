# Complete `send <host>` with online tailnet peers (first status line is this machine); after the host, complete files.
function __send_hosts
    tailscale status 2>/dev/null | tail -n +2 | string match -rv 'offline' | string replace -rf '^\S+\s+(\S+)\s+.*' '$1'
end

complete -c send -f
complete -c send -n '__fish_is_first_arg' -a '(__send_hosts)' -d 'tailnet device'
complete -c send -n '__fish_is_first_arg' -l get -s g -d 'pull received files out of the inbox'
complete -c send -n '__fish_is_first_arg' -l targets -s t -d 'list receivers'
complete -c send -n 'not __fish_is_first_arg' -F
