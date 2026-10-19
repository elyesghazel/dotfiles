"""Shared code for the agenda / rem / ev zunder plugins.

Reads events and reminders through ~/.config/waybar/scripts/gcal (same caches, same
iCloud session) and adds reminders through the `remind` fish function.

    zcal.py refresh                     refresh the reminders cache (runs detached)
    zcal.py done <id> <title>           complete a reminder
    zcal.py add-reminder <title> [iso]  add a reminder, due at iso time if given
"""

import sys

sys.dont_write_bytecode = True  # no __pycache__ next to gcal or in the plugins folder

import datetime as dt  # noqa: E402
import importlib.util  # noqa: E402
import json
import os
import re
import shlex
import subprocess
import urllib.parse
from importlib.machinery import SourceFileLoader
from pathlib import Path

GCAL = Path.home() / ".config/waybar/scripts/gcal"
HERE = Path(__file__).resolve()
PY = "/usr/bin/python3"


def gcal():
    loader = SourceFileLoader("gcal", str(GCAL))
    spec = importlib.util.spec_from_loader("gcal", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def emit(title, subtitle="", hint="", glyph=None, action=None):
    line = {"title": title, "subtitle": subtitle, "hint": hint}
    if glyph:
        line["glyph"] = glyph
    if action:
        line["action"] = action
    print(json.dumps(line), flush=True)


def me(*args):
    """Shell command that runs this file with args."""
    return " ".join(shlex.quote(a) for a in (PY, str(HERE), *args))


def notify(title, body=""):
    subprocess.run(["notify-send", "-a", "zunder", title, body], check=False)


# ── natural dates ──────────────────────────────────────

DAYS = "mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday"
MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december"
WORD = re.compile(
    rf"^(today|tonight|tomorrow|tmrw|tmr|next|this|in|at|on|week|month|noon|midnight|am|pm|"
    rf"{DAYS}|{MONTHS}|"
    r"\d{1,2}(:\d{2})?(am|pm|h)?|"                  # 9  9am  14:00  14h
    r"\d{1,2}(:\d{2})?-\d{1,2}(:\d{2})?|"            # 14:00-15:00 (events)
    r"\d{1,2}\.\d{1,2}\.?(\d{2,4})?|\d{4}-\d{2}-\d{2}|"  # 14.10.  2026-10-14
    r"\d+(min|mins|minutes?|h|hrs?|hours?|d|days?)?|"
    r"min|mins|minutes?|hrs?|hours?|days?|weeks?)$"
)
HAS_TIME = re.compile(r"\d:\d|\d-\d|\d(am|pm|h)\b|\bnoon\b|\bmidnight\b|\btonight\b|\b(min|mins|minutes?|hrs?|hours?)\b|\d+h\b")
ANCHOR = re.compile(rf"\b(today|tonight|tomorrow|tmrw|tmr|{DAYS}|{MONTHS}|noon|midnight)\b|\d:\d|\d(am|pm)\b|\d\.\d|\d{{4}}-|\bin \d")


def gnu_date(text):
    """Text for `date -d`; None if it can't be read."""
    t = text.lower().strip()
    t = re.sub(r"\btmrw?\b", "tomorrow", t)
    t = re.sub(r"\btonight\b", "today 20:00", t)
    t = re.sub(r"\bin (\d+)\s*(min|mins|minutes?)\b", r"+\1 minutes", t)
    t = re.sub(r"\bin (\d+)\s*(h|hrs?|hours?)\b", r"+\1 hours", t)
    t = re.sub(r"\bin (\d+)\s*(d|days?)\b", r"+\1 days", t)
    t = re.sub(r"\b(\d{1,2})h\b(?!\d)", r"\1:00", t)                     # 14h → 14:00
    t = re.sub(r"\b(\d{1,2})\.(\d{1,2})\.?(\d{2,4})?(?!\d)",               # 14.10.(2026) → 2026-10-14
               lambda m: f"{m[3] or dt.date.today().year}-{int(m[2]):02d}-{int(m[1]):02d}", t)
    t = re.sub(r"\b(at|on)\b", " ", t)
    t = re.sub(r"\bnext (" + DAYS + r")\b", r"\1", t)
    r = subprocess.run(["date", "-d", t, "+%Y-%m-%dT%H:%M"], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return dt.datetime.fromisoformat(r.stdout.strip())


def split_when(text, default_hour=9):
    """'call mum tomorrow 18:00' → ('call mum', datetime, has_time). Earliest valid date tail wins."""
    if " @ " in text:
        what, _, when = text.partition(" @ ")
        at = gnu_date(when)
        if at:
            return what.strip(), at, bool(HAS_TIME.search(when.lower()))
    words = text.split()
    for i in range(1, len(words)):
        tail = " ".join(words[i:])
        if all(WORD.match(w.lower()) for w in words[i:]) and ANCHOR.search(tail.lower()):
            # a range like 9-11 or 14:00-15:30: its start is the time
            at = gnu_date(re.sub(r"\b(\d{1,2})(:\d{2})?-\d{1,2}(:\d{2})?\b", lambda m: f"{m[1]}{m[2] or ':00'}", tail))
            if at:
                has_time = bool(HAS_TIME.search(tail.lower()))
                if not has_time:
                    at = at.replace(hour=default_hour, minute=0)
                return " ".join(words[:i]), at, has_time
    return text.strip(), None, False


def time_range(text):
    """'14:00-15:30' anywhere → (start, end) as (h, m) tuples, else None."""
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?-(\d{1,2})(?::(\d{2}))?\b", text)
    if not m:
        return None
    return (int(m[1]), int(m[2] or 0)), (int(m[3]), int(m[4] or 0))


def when_label(at, has_time=True):
    today = dt.date.today()
    day = {today: "today", today + dt.timedelta(days=1): "tomorrow"}.get(at.date(), f"{at:%a %d %b}")
    return f"{day} {at:%H:%M}" if has_time else day


# ── actions ────────────────────────────────────────────

def refresh_detached():
    subprocess.Popen([PY, str(HERE), "refresh"], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main(argv):
    cmd = argv[0] if argv else ""
    if cmd == "refresh":
        try:
            gcal().fetch_reminders()
        except Exception:
            pass
    elif cmd == "done":
        rem_id, title = argv[1], argv[2]
        try:
            gcal().complete(rem_id)
            notify("Reminder done", title)
        except Exception as e:
            notify("Couldn't complete reminder", str(e))
        refresh_detached()
    elif cmd == "add-reminder":
        title = argv[1]
        args = [title] + (["@", argv[2].replace("T", " ")] if len(argv) > 2 else [])
        r = subprocess.run(["fish", "-c", "remind $argv"] + args, capture_output=True, text=True)
        if r.returncode == 0:
            notify("Reminder added", title + (f" · {argv[2].replace('T', ' ')}" if len(argv) > 2 else ""))
        else:
            notify("Couldn't add reminder", (r.stderr or r.stdout).strip()[-200:])
        refresh_detached()


def google_event_url(title, start, end, all_day, where=""):
    if all_day:
        dates = f"{start:%Y%m%d}/{end:%Y%m%d}"
    else:
        dates = f"{start:%Y%m%dT%H%M%S}/{end:%Y%m%dT%H%M%S}"
    tz = os.path.realpath("/etc/localtime").split("zoneinfo/")[-1]
    q = {"action": "TEMPLATE", "text": title, "dates": dates, "ctz": tz}
    if where:
        q["location"] = where
    return "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(q)


if __name__ == "__main__":
    main(sys.argv[1:])
