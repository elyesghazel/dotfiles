#!/usr/bin/env python3
"""Survey a folder of clips: table of specs + a contact sheet per clip.

    survey.py <footage-dir> [--sheets-dir DIR] [--every 2]

Read the sheets as images afterwards. You cannot edit footage you have not seen.
"""
import argparse, glob, json, os, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--sheets-dir", default="work/sheets")
ap.add_argument("--every", type=float, default=2.0, help="seconds between sheet frames")
ap.add_argument("--cols", type=int, default=5)
ap.add_argument("--max-rows", type=int, default=12, help="cap sheet height")
a = ap.parse_args()

EXTS = ("mp4", "MP4", "mov", "MOV", "mkv", "MKV", "m4v", "M4V", "insv", "INSV", "avi", "AVI")
files = sorted(set(sum((glob.glob(os.path.join(a.dir, "*." + e)) for e in EXTS), [])))
if not files:
    sys.exit(f"no mp4s in {a.dir}")
os.makedirs(a.sheets_dir, exist_ok=True)

print("%-16s %8s %10s %6s %6s %6s %-20s %9s" %
      ("FILE", "DUR", "RES", "FPS", "VIDEO", "AUDIO", "CREATED", "BITRATE"))
total = 0.0
for f in files:
    out = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                          "-show_format", "-show_streams", f],
                         capture_output=True, text=True).stdout
    # GoPro writes raw control characters into tags -> strict=False
    d = json.loads(out, strict=False)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    if v is None:
        print("%-16s  (no video stream — skipped)" % os.path.basename(f)); continue
    au = [s for s in d["streams"] if s["codec_type"] == "audio"]
    fm = d["format"]
    n, de = v["r_frame_rate"].split("/")
    dur = float(fm.get("duration") or 0.0); total += dur
    br = int(fm.get("bit_rate") or 0) / 1e6
    print("%-16s %8.2f %10s %6.2f %6s %6s %-20s %6.1f Mb" % (
        os.path.basename(f), dur, "%sx%s" % (v["width"], v["height"]),
        float(n) / float(de), v["codec_name"], au[0]["codec_name"] if au else "NONE",
        fm.get("tags", {}).get("creation_time", "?")[:19], br))

    # cap the sheet: a 30-min clip at --every 2 would be 5x181 tiles (44000 px tall)
    every = a.every
    if dur / every > a.cols * a.max_rows:
        every = dur / (a.cols * a.max_rows)
    rows = max(1, min(a.max_rows, int(dur / every / a.cols) + 1))
    sheet = os.path.join(a.sheets_dir, os.path.splitext(os.path.basename(f))[0] + ".jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-frames:v", "1",
                    "-vf", f"fps=1/{every},scale=440:-2,tile={a.cols}x{rows}", sheet],
                   check=False)

print("\nTOTAL %.1f s = %d:%02d across %d clips" % (total, total // 60, total % 60, len(files)))
print("contact sheets -> %s/  (read them as images)" % a.sheets_dir)
