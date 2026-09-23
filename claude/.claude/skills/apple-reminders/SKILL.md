---
name: apple-reminders
description: Read and write Elyes' Apple Reminders (iCloud) from Linux through the pyicloud CLI, wrapped by the `remind` and `icloud` fish functions. This is where todos go. Use whenever the user says "remind me", "add a reminder", "create a todo / task", "todo: X", "I need to X", "don't let me forget X", "put X on my list", "what's on my reminders", "what do I have to do", "tick off / mark done / complete X", or mentions Apple Reminders, iCloud reminders, or their iPhone to-dos. Also use for setting due dates on existing reminders, deleting reminders, or when an `icloud` command fails with an auth or session error.
---

# Apple Reminders

Reminders live in iCloud and sync to the iPhone. On this Arch box they are reached through
**pyicloud** (`uv tool install 'pyicloud[cli]' --with rich`), which talks to iCloud's
unofficial web API. Two fish functions sit on top:

- `icloud` — the pyicloud CLI with its session kept in `~/.local/state/pyicloud/` rather
  than `/tmp`. Always go through it; the bare binary looks in `/tmp` and finds no session.
- `remind` — the everyday add / list / complete helper.

The Bash tool runs bash, so call them as `fish -c '...'`.

## Reminders or calendar?

Todos, tasks and nudges go here; things that *happen* at a time (appointments, meetings,
dinners, exams — anything with a duration, a place or other people) go to Google Calendar via
the `Google_Calendar` connector's `create_event`. "Go shopping" and "pay rent by Friday" are
reminders; "dentist Tuesday 14:00" is an event. Titles stay short and imperative, the way
they'd read on the phone: "Go shopping", not "Reminder to go shopping".

## Everyday: `remind`

```bash
fish -c 'remind'                                  # open reminders, numbered, soonest first
fish -c 'remind buy oat milk'                     # add, no due date
fish -c 'remind call mum @ tomorrow 18:00'        # add with a due date
fish -c 'remind --done 2'                         # complete #2 from the listing
```

- Everything after the last standalone `@` is passed to GNU `date -d`, so "fri 9am",
  "next monday 14:00", "2026-10-01 08:30" all work. Convert the user's phrasing into one of
  those rather than guessing a timestamp.
- "Remind me at 9" with no day means today if 9:00 is still ahead, otherwise tomorrow —
  pick one and say which.
- `--done` numbers come from a fresh `remind` listing. List first, then complete by number;
  never reuse a number from earlier in the conversation, the order shifts as items change.

## Anything else: `icloud reminders`

`remind` covers add/list/done on the default list. For the rest use the full CLI — every
subcommand takes `--format json`, and `--log-level error` hides a harmless
`Unsupported AlarmTrigger type 'Date'` warning.

| Need | Command |
|---|---|
| Lists and their ids | `icloud reminders lists --format json` |
| Reminders incl. completed | `icloud reminders list --include-completed --format json` |
| One list only | `icloud reminders list --list-id List/<uuid>` |
| Change title / due / notes | `icloud reminders update <Reminder/id> --title … --due-date …` |
| Delete | `icloud reminders delete <Reminder/id>` |
| Flag, priority, notes on create | `icloud reminders create --list-id … --title … --flagged --priority 1 --desc …` |
| Alarms, recurrence, subtasks | `icloud reminders alarm/recurrence --help`, `create --parent-reminder-id` |

Due dates need two things. First, an offset: pyicloud reads a naive time as **UTC**, so
`2026-10-01T09:00` lands at 11:00 in Zurich. Build it with
`date -d "<when>" --iso-8601=seconds`. Second, `--time-zone Europe/Zurich` (or whatever
`timedatectl show -p Timezone --value` says). Without one, the iPhone shows the reminder at
its UTC time, two hours early. Apple priorities: 1 high, 5 medium, 9 low, 0 none.

Ask before deleting — there is no undo. Completing is fine without asking when the user
clearly named the item.

## When auth breaks

`icloud auth status` shows the session. Apple expires trusted sessions every few weeks; a
"requires re-authentication" error means the user must log in again — it needs their
password and a 2FA prompt on the iPhone, so hand them the command rather than running it:

```
! icloud auth login --username elyes@elyesghazel.ch
```

If login succeeds but Reminders returns nothing or 403s, check the iPhone: **Access iCloud
Data on the Web** must be on and **Advanced Data Protection** off.
