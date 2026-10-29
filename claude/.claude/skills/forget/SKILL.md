---
name: forget
description: Keep the current chat out of memory for good - drop it from the recall index and every recall mode (search, --list, --show, so the nightly dream never reads it) and write nothing about it to ~/ai. Use when the user types /forget, or says "don't remember this chat", "forget this session", "don't save this", "keep this out of memory", "off the record", "vergiss diesen Chat", "nicht speichern". Also for undoing it ("remember that chat again", /forget undo) or listing forgotten chats.
---

# forget: keep a chat out of memory

Run on the VPS, inside the session being forgotten:

```sh
recall --forget              # this session (uses $CLAUDE_CODE_SESSION_ID)
recall --forget <id-prefix>  # another session, ids from `recall --list`
recall --unforget <id>       # undo; it is re-indexed on the next `recall --index`
recall --forgotten           # list forgotten sessions with titles
```

`--forget` adds the full id to `~/.local/state/recall/forgotten`, deletes its chunks from
`~/.cache/recall/index.sqlite` and from then on every recall mode skips it, including turns
added after the command. The nightly dream only reads sessions through recall, so it never
sees it either.

After running it, for the rest of this chat:

- Write nothing from it to `~/ai`: no memory file, no MEMORY.md line, no diary bullet.
- If the chat changed a machine (service, cron, config), say that its `changelog.md` /
  `map.md` entry is skipped too and offer to add a neutral one-line entry, because those files
  are how later sessions find what is running. Add it only if he says yes.
- Confirm in one line with the session title, and mention that the raw transcript file
  (`~/.claude*/projects/.../<id>.jsonl`) still exists on disk; offer to delete it only if he
  wants it gone completely (deleting also breaks resuming the chat).

Never forget a session the user did not ask about. A forgotten id that no longer has a
transcript stays in the list on purpose, so a restored file does not come back silently.
