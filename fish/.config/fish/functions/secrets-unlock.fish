function secrets-unlock --description 'Unlock Vaultwarden for the `secrets` CLI in this shell'
    if not command -q bw
        echo "bw not installed - see ~/dotfiles/docs/secrets.md (standalone 2026.7.0)" >&2
        return 1
    end
    set -l session (bw unlock --raw)
    or return 1
    if test -z "$session"
        echo "bw unlock returned no session key - run `bw unlock` in a real terminal to see why" >&2
        return 1
    end
    set -gx BW_SESSION $session
    echo "unlocked - `secrets status` to see this host, `bw lock` when done"
end
