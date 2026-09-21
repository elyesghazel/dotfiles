# ~/.config/fish/functions/clip.fish
# Purpose: Push a short piece of TEXT to the phone as an ntfy notification, so it
#          can be copied with one tap. Taildrop can only deliver files, not the
#          phone's clipboard - for a URL, a code, an address, this is faster.
# Usage:   clip <text...>          clip "https://example.com/x"
#          <cmd> | clip            wl-paste | clip
#          clip                    (no args, no pipe) sends the desktop clipboard
#
# Config: NTFY_URL / NTFY_TOPIC / NTFY_TOKEN in ~/.claude/secrets.fish (gitignored).
# Uses --data-binary so newlines survive (curl -d strips them - see the /daily brief).

function clip --description 'Send text to the phone via ntfy'
    test -f ~/.claude/secrets.fish; and source ~/.claude/secrets.fish
    if test -z "$NTFY_URL" -o -z "$NTFY_TOPIC" -o -z "$NTFY_TOKEN"
        echo "clip: set NTFY_URL, NTFY_TOPIC and NTFY_TOKEN in ~/.claude/secrets.fish" >&2
        return 1
    end

    set -l text
    if test (count $argv) -gt 0
        set text (string join ' ' -- $argv)
    else if not isatty stdin
        # fish 4: a command substitution in a function does not see piped stdin, so read -z.
        read -z text
        set text (string trim --right --chars \n -- $text)
    else if type -q wl-paste
        set text (wl-paste --no-newline)
    else if type -q xclip
        set text (xclip -selection clipboard -o)
    else
        echo "clip: nothing to send (no args, no pipe, no clipboard tool)" >&2
        return 1
    end
    set text (string join \n -- $text)
    test -z "$text"; and echo "clip: empty" >&2; and return 1

    printf '%s' "$text" | curl -fsS -o /dev/null \
        -H "Authorization: Bearer $NTFY_TOKEN" \
        -H "Title: clip from "(hostname) \
        -H "Tags: clipboard" \
        --data-binary @- "$NTFY_URL/$NTFY_TOPIC"
    and echo "clip: sent "(string length -- "$text")" chars"
end
