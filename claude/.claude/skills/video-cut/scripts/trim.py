#!/usr/bin/env python3
"""edl.json -> public/clips/*.mp4, each cut, graded and levelled.

    GOPRO_SRC=/path/to/footage trim.py [--only id1,id2]

Re-encodes with dense keyframes (-g 15) so the renderer can seek cheaply.
See references/audio.md for the profiles.
"""
import argparse, json, os, subprocess, sys

SRC = os.environ.get("GOPRO_SRC", "footage")

GRADES = {
    "base":   "eq=contrast=1.06:saturation=1.10:gamma=1.02",
    "hot":    "eq=contrast=1.10:saturation=1.12:gamma=0.90:brightness=-0.045",
    "shade":  "eq=contrast=1.05:saturation=1.12:gamma=1.10:brightness=0.020",
    "dark":   "eq=contrast=1.12:saturation=1.05:gamma=1.30:brightness=0.045",
    "golden": "eq=contrast=1.08:saturation=1.16:gamma=1.02,colorbalance=rm=0.04:gh=0.01:bs=-0.03",
    "dusk":   "eq=contrast=1.10:saturation=1.18:gamma=1.12:brightness=0.015,colorbalance=rm=0.05:bs=-0.04",
}
AUDIO = {
    "voice": ("highpass=f=110,afftdn=nf=-25,"
              "acompressor=threshold=-20dB:ratio=3:attack=15:release=250:makeup=2,"
              "loudnorm=I=-16:TP=-1.5:LRA=11"),
    "amb":   "highpass=f=100,loudnorm=I=-22:TP=-2:LRA=11",
    "ride":  "highpass=f=90,loudnorm=I=-24:TP=-2:LRA=11",
}

ap = argparse.ArgumentParser()
ap.add_argument("--edl", default="edl.json")
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--crf", type=int, default=18)
ap.add_argument("--only", default=None, help="comma-separated ids to rebuild")
ap.add_argument("--src", default=None, help="footage dir (overrides $GOPRO_SRC)")
ap.add_argument("--out", default="public/clips")
a = ap.parse_args()

SRC = a.src or SRC
OUT = a.out
os.makedirs(OUT, exist_ok=True)
edl = json.load(open(a.edl))
ids = {c["id"] for c in edl}
only = set(a.only.split(",")) if a.only else None
if only:
    unknown = only - ids
    if unknown:                       # a typo must not look like success
        sys.exit(f"--only: no such id(s): {', '.join(sorted(unknown))}\n"
                 f"known: {', '.join(sorted(ids))}")

for c in edl:
    if only and c["id"] not in only:
        continue
    # a clip can live in a different date folder (camera clock errors, misfiles)
    # "dir" may be absolute, or relative to SRC's parent (sibling date folder)
    if c.get("dir"):
        src_dir = c["dir"] if os.path.isabs(c["dir"]) else \
            os.path.join(os.path.dirname(os.path.abspath(SRC.rstrip("/"))), c["dir"])
    else:
        src_dir = SRC
    src = os.path.join(src_dir, c["src"] + ".mp4")
    if not os.path.exists(src):
        sys.exit(f"missing source: {src}")
    dst = os.path.join(OUT, c["id"] + ".mp4")
    if c["grade"] not in GRADES:
        sys.exit(f"{c['id']}: unknown grade {c['grade']!r}. valid: {', '.join(GRADES)}")
    if c["aud"] not in AUDIO:
        sys.exit(f"{c['id']}: unknown aud {c['aud']!r}. valid: {', '.join(AUDIO)}")
    vf = GRADES[c["grade"]] + f",fps={a.fps},format=yuv420p"
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", str(c["in"]), "-i", src,
         "-t", str(c["dur"]), "-vf", vf, "-af", AUDIO[c["aud"]],
         "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf),
         "-g", "15", "-keyint_min", "15",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", dst], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FAIL {c['id']}\n{r.stderr[-600:]}")
    print(f"ok {c['id']:<15} {os.path.getsize(dst)/1e6:6.1f} MB  [{c['grade']}/{c['aud']}]")
