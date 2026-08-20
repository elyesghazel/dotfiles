#!/usr/bin/env python3
"""Map the transcript onto FILM time -> speech.json.

    speechmap.py

Produces where the music must duck ("spans"), where it may breathe (printed as
gaps), and where it should duck harder ("quiet", from banter.json).
"""
import argparse, json, os

ap = argparse.ArgumentParser()
ap.add_argument("--edl", default="edl.json")
ap.add_argument("--timeline", default="src/timeline.json")
ap.add_argument("--transcript", default="work/transcript.json")
ap.add_argument("--banter", default="banter.json")
ap.add_argument("--out", default="speech.json")
a = ap.parse_args()

tr = json.load(open(a.transcript))
edl = {c["id"]: c for c in json.load(open(a.edl))}
tl = json.load(open(a.timeline))
FPS = tl["fps"]

spans = []
for c in tl["clips"]:
    e = edl[c["id"]]; I, D, F = e["in"], e["dur"], c["start"] / FPS
    for s in tr.get(e["src"], {}).get("segments", []):
        x, y = max(s["s"], I), min(s["e"], I + D)
        if y - x >= 0.35:
            spans.append([round(F + (x - I), 2), round(F + (y - I), 2), s["t"]])
spans.sort()

merged = []
for s in spans:                                   # <0.8s apart = one talking block
    if merged and s[0] - merged[-1][1] < 0.8:
        merged[-1][1] = max(merged[-1][1], s[1]); merged[-1][2] += " " + s[2]
    else:
        merged.append(list(s))

quiet = []
if os.path.exists(a.banter):
    for b in json.load(open(a.banter)):
        for c in tl["clips"]:
            e = edl[c["id"]]
            if e["src"] != b["src"]:
                continue
            I, D, F = e["in"], e["dur"], c["start"] / FPS
            x, y = max(b["s"], I), min(b["e"], I + D)
            if y - x > 0.3:
                quiet.append([round(F + (x - I), 2), round(F + (y - I), 2)])
    quiet.sort()

total = tl["total"] / FPS
talk = sum(b - x for x, b, _ in merged)
json.dump({"total": total, "spans": [[x, y] for x, y, _ in merged], "quiet": quiet},
          open(a.out, "w"), indent=1)
print(f"film {total:.1f}s | speech {talk:.1f}s ({talk/total*100:.0f}%) | {len(merged)} blocks\n")
for x, y, t in merged:
    print(f"  {int(x//60)}:{x%60:05.2f} - {int(y//60)}:{y%60:05.2f} ({y-x:5.1f}s)  {t[:70]}")
prev, gaps = 0.0, []
for x, y, _ in merged:
    if x - prev > 1.2:
        gaps.append((prev, x))
    prev = y
if total - prev > 1.2:
    gaps.append((prev, total))
print(f"\nmusic-forward gaps ({len(gaps)}):")
for x, y in gaps:
    print(f"  {int(x//60)}:{x%60:05.2f} - {int(y//60)}:{y%60:05.2f}  ({y-x:5.1f}s)")
if quiet:
    print(f"\nextra-duck windows ({len(quiet)}):")
    for x, y in quiet:
        print(f"  {int(x//60)}:{x%60:05.2f} - {int(y//60)}:{y%60:05.2f}  ({y-x:.1f}s)")
