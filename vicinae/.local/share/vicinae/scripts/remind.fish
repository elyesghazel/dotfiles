#!/usr/bin/env fish
# @vicinae.schemaVersion 1
# @vicinae.title Remind
# @vicinae.description Add an Apple Reminder (when: anything `date -d` reads)
# @vicinae.packageName Reminders
# @vicinae.icon ⏰
# @vicinae.mode compact
# @vicinae.argument1 { "type": "text", "placeholder": "what" }
# @vicinae.argument2 { "type": "text", "placeholder": "when", "optional": true }

# Thin shim over the remind fish function, which owns the logic. compact mode
# shows the last line as a toast, so remind's one-line confirmation is the UI.
# stderr is folded in so a rejected time shows up in the toast too.
if test -n "$argv[2]"
    remind $argv[1] @ $argv[2] 2>&1
else
    remind $argv[1] 2>&1
end
