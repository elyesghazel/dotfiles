# ~/.config/fish/functions/remind.fish
# Purpose: Add, list and tick off Apple Reminders from Linux, via pyicloud.
# Usage:   remind                          list open reminders, numbered, soonest first
#          remind <text...>                add to the default list, no due date
#          remind <text...> @ <when>       add with a due date (remind call mum @ tomorrow 18:00)
#          remind --done <n>               complete reminder <n> from the listing
#
# <when> is anything GNU `date -d` understands ("tomorrow 9am", "fri 14:00",
# "2026-10-01 08:30"). It is sent with the local offset - pyicloud treats a
# naive time as UTC, which would land two hours off in Zurich.
# Default list is the first one iCloud returns; pin another with $REMIND_LIST_ID.
# Session handling lives in the icloud wrapper (icloud.fish).

# Runs an icloud query and prints its JSON. Retries once: iCloud now and then
# answers with an empty body, and json.load on "" is a traceback, not an error.
function __remind_json
    set -l err (mktemp)
    for attempt in 1 2
        set -l out (icloud $argv --format json --log-level error 2>$err | string collect)
        if test $pipestatus[1] -eq 0 -a -n "$out"
            rm -f $err
            printf '%s\n' $out
            return 0
        end
    end
    echo "remind: iCloud gave no answer - "(string join ' ' -- (tail -n3 $err)) >&2
    rm -f $err
    return 1
end

function remind --description 'Apple Reminders: add, list, complete'
    # pyicloud's own venv has Python for JSON; there is no jq on this box.
    set -l py ~/.local/share/uv/tools/pyicloud/bin/python
    if not test -x $py
        echo "remind: pyicloud not installed - uv tool install 'pyicloud[cli]' --with rich" >&2
        return 1
    end

    # Prints "id<TAB>due<TAB>title" for open reminders, soonest first, undated last.
    set -l list_open "
import json, sys
from datetime import datetime
rows = [r for r in json.load(sys.stdin) if not r['completed'] and not r['deleted']]
key = lambda r: (r['due_date'] is None, r['due_date'] or '')
for r in sorted(rows, key=key):
    due = ''
    if r['due_date']:
        due = datetime.fromisoformat(r['due_date'].replace('Z', '+00:00')).astimezone().strftime('%a %d %b %H:%M')
    print(r['id'], due, r['title'], sep='\t')
"

    if test (count $argv) -eq 0
        set -l json (__remind_json reminders list); or return 1
        set -l rows (printf '%s\n' $json | $py -c $list_open); or return 1
        if test (count $rows) -eq 0
            echo "remind: nothing open"
            return 0
        end
        for i in (seq (count $rows))
            set -l f (string split \t -- $rows[$i])
            printf '%2d  %-16s  %s\n' $i "$f[2]" "$f[3]"
        end
        return 0
    end

    if test "$argv[1]" = --done
        if not string match -qr '^\d+$' -- "$argv[2]"
            echo "remind: --done takes the number from the listing" >&2
            return 1
        end
        set -l json (__remind_json reminders list); or return 1
        set -l rows (printf '%s\n' $json | $py -c $list_open); or return 1
        if test $argv[2] -lt 1 -o $argv[2] -gt (count $rows)
            echo "remind: no reminder $argv[2]" >&2
            return 1
        end
        set -l f (string split \t -- $rows[$argv[2]])
        icloud reminders set-status $f[1] --completed --log-level error >/dev/null
        and echo "remind: done - $f[3]"
        return
    end

    # Split "<text> @ <when>" on the last standalone @.
    set -l title $argv
    set -l when
    set -l at (contains -i -- @ $argv | tail -n1)
    if test -n "$at"
        set title $argv[1..(math $at - 1)]
        test $at -lt (count $argv); and set when $argv[(math $at + 1)..-1]
    end
    set title (string join ' ' -- $title)
    if test -z "$title"
        echo "remind: nothing to remind about" >&2
        return 1
    end

    set -l due_args
    if test -n "$when"
        # date -d rejects the Swiss "18.00"; make it "18:00".
        set when (string replace -ra '\b(\d{1,2})\.(\d{2})\b' '$1:$2' -- "$when")
        set -l due (date -d "$when" --iso-8601=seconds 2>/dev/null)
        if test -z "$due"
            echo "remind: can't read the time '$when'" >&2
            return 1
        end
        # Without a TimeZone the iPhone shows the UTC wall clock (18:00 -> 16:00).
        set -l tz (timedatectl show -p Timezone --value 2>/dev/null)
        test -n "$tz"; or set tz (readlink -f /etc/localtime | string replace -r '.*/zoneinfo/' '')
        set due_args --due-date $due --time-zone $tz
    end

    set -l list_id $REMIND_LIST_ID
    if test -z "$list_id"
        set -l json (__remind_json reminders lists); or return 1
        set list_id (printf '%s\n' $json | $py -c 'import json,sys; print(next(l["id"] for l in json.load(sys.stdin) if not l["deleted"]))')
        or return 1
    end

    icloud reminders create --list-id $list_id --title "$title" $due_args --log-level error >/dev/null
    or return 1
    if test -n "$when"
        echo "remind: $title - "(date -d "$when" '+%a %d %b %H:%M')
    else
        echo "remind: $title"
    end
end
