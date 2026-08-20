#!/usr/bin/env python3
"""edl.json -> src/timeline.json: frame-accurate starts, dissolves, audio fades.

    timeline.py [--dissolve 20] [--fps 30]

Dissolve into a shot when its act differs from the previous one, or when it is
marked {"diss": true} (use for jump cuts inside one source clip). Hard cuts
elsewhere — dissolving every join looks unedited.
"""
import argparse, json, os

ap = argparse.ArgumentParser()
ap.add_argument("--edl", default="edl.json")
ap.add_argument("--out", default="src/timeline.json")
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--dissolve", type=int, default=20)
ap.add_argument("--width", type=int, default=1920)
ap.add_argument("--height", type=int, default=1080)
a = ap.parse_args()

edl = json.load(open(a.edl))
if not edl:
    raise SystemExit(f"{a.edl} is empty")
t, out = 0, []
for i, c in enumerate(edl):
    d = 0
    if i > 0 and (c.get("diss") or c["act"] != edl[i - 1]["act"]):
        d = a.dissolve
        t -= d
    dur = round(c["dur"] * a.fps)
    out.append({"id": c["id"], "act": c["act"], "start": t, "dur": dur,
                "fadeIn": d, "fadeOut": 0, "src": f"clips/{c['id']}.mp4"})
    t += dur

for i in range(len(out) - 1):
    out[i]["fadeOut"] = out[i + 1]["fadeIn"]
out[-1]["fadeOut"] = 45          # ride the last one out with the picture

os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
json.dump({"fps": a.fps, "width": a.width, "height": a.height,
           "total": t, "clips": out}, open(a.out, "w"), indent=1)
print(f"total {t} frames = {t/a.fps:.2f}s = {int(t/a.fps)//60}:{int(t/a.fps)%60:02d}")
for c in out:
    print(f"  {c['start']:>5} +{c['dur']:>4} in{c['fadeIn']:>3} out{c['fadeOut']:>3}  "
          f"{c['id']:<15} {c['act']}")
