#!/usr/bin/env python3
"""Transcribe every clip so cuts can land on sentence boundaries.

    transcribe.py <footage-dir> [--model small] [--out work/transcript.json]

Needs faster-whisper (`pip install faster-whisper` in a venv). Merges into an
existing transcript.json, so extra clips found later can be added cheaply.
"""
import argparse, glob, json, os, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--model", default="small")
ap.add_argument("--out", default="work/transcript.json")
ap.add_argument("--wav-dir", default="work/wav")
a = ap.parse_args()

try:
    from faster_whisper import WhisperModel
except ImportError:
    sys.exit("pip install faster-whisper")

os.makedirs(a.wav_dir, exist_ok=True)
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
tr = json.load(open(a.out)) if os.path.exists(a.out) else {}

m = WhisperModel(a.model, device="cpu", compute_type="int8",
                 cpu_threads=max(1, (os.cpu_count() or 4) - 1))
EXTS = ("mp4", "MP4", "mov", "MOV", "mkv", "MKV", "m4v", "M4V", "insv", "INSV", "avi", "AVI")
files = sorted(set(sum((glob.glob(os.path.join(a.dir, "*." + e)) for e in EXTS), [])))
for f in files:
    b = os.path.splitext(os.path.basename(f))[0]
    if b in tr:
        continue
    w = os.path.join(a.wav_dir, b + ".wav")
    # never reuse a wav from an interrupted run — extract to a temp name and rename
    if not os.path.exists(w) or os.path.getsize(w) < 1024:
        tmp = w + ".part"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vn", "-ac", "1",
                        "-ar", "16000", "-c:a", "pcm_s16le", tmp], check=True)
        os.replace(tmp, w)
    segs, info = m.transcribe(w, vad_filter=True,
                              vad_parameters=dict(min_silence_duration_ms=350),
                              beam_size=5, condition_on_previous_text=False)
    segs = list(segs)
    tr[b] = {"lang": info.language, "lang_p": round(info.language_probability, 2),
             "segments": [{"s": round(s.start, 2), "e": round(s.end, 2),
                           "t": s.text.strip()} for s in segs]}
    json.dump(tr, open(a.out, "w"), ensure_ascii=False, indent=1)   # save per clip:
    # a failure on clip 29 of 30 must not discard the previous 29
    print(f"--- {b}  [{info.language} {info.language_probability:.2f}]  {len(segs)} seg")
    for s in segs:
        print(f"    {s.start:6.2f}-{s.end:6.2f}  {s.text.strip()}")

json.dump(tr, open(a.out, "w"), ensure_ascii=False, indent=1)
print(f"\n-> {a.out}  ({len(tr)} clips)")
print("Snap every EDL in/out to one of these boundaries.")
