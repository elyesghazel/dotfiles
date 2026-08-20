#!/usr/bin/env python3
"""Audio master: dialogue timeline + an arranged, speech-ducked music bed.

    score.py --music song.mp3 --preview work/master.mp3     # audio only, no video
    score.py --music song.mp3 --mux out/picture.mp4 \
             --out out/film.mp4                             # finished film

Deliberately OUTSIDE the picture render. The render takes tens of minutes; this
takes seconds, so the music can be re-tuned without re-rendering a frame. The
mux copies the video stream.

Never source the music yourself — the user supplies a file they own.
"""
import argparse, json, os, subprocess, sys, tempfile, wave
import numpy as np

SR = 48000
ap = argparse.ArgumentParser()
ap.add_argument("--music", default=os.environ.get("VLOG_MUSIC"))
ap.add_argument("--timeline", default="src/timeline.json")
ap.add_argument("--speech", default="speech.json")
ap.add_argument("--clips", default="public/clips")
ap.add_argument("--mux", default=None, help="rendered picture to mux into")
ap.add_argument("--out", default="out/final.mp4")
ap.add_argument("--preview", metavar="PATH", default=None,
                help="write the audio master to this mp3 path")
ap.add_argument("--enter", type=float, default=None,
                help="film time to bring music in (default: end of first speech block)")
ap.add_argument("--lead-at", type=float, default=None,
                help="film time the music takes the lead (default: end of the last "
                     "long speech block — a heuristic, override for other shapes)")
ap.add_argument("--xf", type=float, default=2.0, help="splice crossfade seconds")
# levels, in dB relative to the measured dialogue level
ap.add_argument("--db-under", type=float, default=-14.0)
ap.add_argument("--db-banter", type=float, default=-23.0)
ap.add_argument("--db-gap", type=float, default=-2.0)
ap.add_argument("--db-lead", type=float, default=+2.0)
a = ap.parse_args()

if not a.music:
    sys.exit("no --music (and no VLOG_MUSIC set). The user must supply a file they own — "
             "never source copyrighted music yourself.")
if not os.path.exists(a.music):
    sys.exit(f"music file not found: {a.music}")

tl = json.load(open(a.timeline)); FPS = tl["fps"]
sp = json.load(open(a.speech)); SPANS = sp["spans"]; QUIET = sp.get("quiet", [])
N = int(round(tl["total"] / FPS * SR)); DUR = N / SR


def dec(path, ss=0.0, t=None):
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if ss:
        cmd += ["-ss", f"{ss:.4f}"]
    cmd += ["-i", path]
    if t:
        cmd += ["-t", f"{t:.4f}"]
    cmd += ["-vn", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_s16le", "-f", "wav", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    i = raw.find(b"data")
    return (np.frombuffer(raw[i + 8:], "<i2").astype(np.float32) / 32768.0).reshape(-1, 2)


def smooth(x, k, passes=3):
    """O(n) box smoothing, repeated -> near-Gaussian. np.convolve with a ~50k-tap
    kernel over millions of samples is O(n*k) and takes minutes."""
    k = max(3, int(k) // passes | 1)
    for _ in range(passes):
        pad = k // 2
        xp = np.concatenate((np.full(pad, x[0]), x, np.full(pad, x[-1])))
        c = np.cumsum(np.concatenate(([0.0], xp)))
        x = ((c[k:] - c[:-k]) / k)[:len(x)]
    return x.astype(np.float32)


# ---- 1. dialogue timeline, exactly as the composition lays it out ------------
dia = np.zeros((N, 2), dtype=np.float32)
for c in tl["clips"]:
    seg = dec(os.path.join(a.clips, os.path.basename(c["src"])))
    n = min(len(seg), c["dur"] * SR // FPS); seg = seg[:n]
    aIn = max(c["fadeIn"], 5) * SR // FPS
    aOut = max(c["fadeOut"], 5) * SR // FPS
    env = np.ones(n, dtype=np.float32)
    env[:aIn] = np.linspace(0, 1, aIn, dtype=np.float32)
    env[n - aOut:] = np.linspace(1, 0, aOut, dtype=np.float32)
    s = c["start"] * SR // FPS
    dia[s:s + n] += seg * env[:, None]

# ---- 2. arrange: land the song's ending on the film's ending -----------------
song = dec(a.music); SL = len(song) / SR
if not SPANS and (a.enter is None or a.lead_at is None):
    sys.exit("speech.json has no speech spans. For a film with no dialogue, pass both "
             "--enter and --lead-at explicitly.")
ENTER = a.enter if a.enter is not None else SPANS[0][1] + 0.05
if a.lead_at is not None:
    LEAD_AT = a.lead_at
elif len(SPANS) >= 2:
    LEAD_AT = SPANS[-2][1]          # heuristic: end of the last long speech block
else:
    LEAD_AT = DUR * 0.8


def onsets(x, H=512):
    m = x.mean(1); n = len(m) // H
    S = np.abs(np.fft.rfft(m[:n * H].reshape(n, H) * np.hanning(H), axis=1))
    d = np.diff(S, axis=0); d[d < 0] = 0
    return d.sum(1), H


def snap(t, env, H, win=1.2):
    i = int(t * SR / H); w = int(win * SR / H)
    lo, hi = max(0, i - w), min(len(env), i + w)
    return t if hi <= lo else (lo + int(np.argmax(env[lo:hi]))) * H / SR


oe, H = onsets(song)
lenB = DUR - LEAD_AT + a.xf
inB = snap(max(0.0, SL - lenB - 0.35), oe, H)     # song's own fade ends with the film
lenA = LEAD_AT - ENTER + a.xf
inA = snap(max(4.0, min(12.0, SL * 0.04)), oe, H, win=1.0)  # past a quiet intro build

bed = np.zeros((N, 2), dtype=np.float32)


def place(src_t, film_t, length, fin, fout):
    n = int(length * SR); s = int(film_t * SR)
    seg = song[int(src_t * SR):int(src_t * SR) + n]
    if len(seg) < n:
        seg = np.pad(seg, ((0, n - len(seg)), (0, 0)))
    e = np.ones(n, dtype=np.float32)
    if fin:
        k = int(fin * SR);  e[:k] = np.sin(np.linspace(0, np.pi / 2, k, dtype=np.float32)) ** 2
    if fout:
        k = int(fout * SR); e[-k:] = np.cos(np.linspace(0, np.pi / 2, k, dtype=np.float32)) ** 2
    m = min(n, N - s)
    bed[s:s + m] += seg[:m] * e[:m, None]


place(inA, ENTER, lenA, 1.6, a.xf)
place(inB, LEAD_AT - a.xf, lenB, a.xf, 0.0)

# ---- 3. duck, referenced to the measured dialogue level ----------------------
t = np.arange(N, dtype=np.float32) / SR
mask = np.zeros(N, dtype=bool)
for s, e in SPANS:
    mask[int(s * SR):int(e * SR)] = True
if not mask.any():
    sys.exit("no speech samples to reference the music level against — pass --enter/--lead-at "
             "and set levels manually, or check speech.json")
dia_ref = 20 * np.log10(np.sqrt((dia.mean(1)[mask] ** 2).mean()) + 1e-9)
if not np.isfinite(dia_ref):
    sys.exit(f"dialogue reference level is {dia_ref} — refusing to write a nan master")
nz = bed.mean(1) != 0
bed *= 10 ** ((-18.0 - 20 * np.log10(np.sqrt((bed.mean(1)[nz] ** 2).mean()) + 1e-9)) / 20)

lvl = lambda db: 10 ** ((dia_ref + db + 18.0) / 20)
g = np.full(N, lvl(a.db_gap), dtype=np.float64)
g[t >= LEAD_AT] = lvl(a.db_lead)
for s, e in SPANS:
    g[(t >= s - 0.35) & (t <= e + 0.45)] = lvl(a.db_under)
for s, e in QUIET:
    g[(t >= s - 0.30) & (t <= e + 0.40)] = lvl(a.db_banter)
g[t < ENTER] = 0.0
g = smooth(g, int(1.1 * SR))
g[t < ENTER - 0.15] = 0.0
bed *= g[:, None]

mix = dia * 0.97 + bed
pk = np.abs(mix).max()
if pk > 0.97:
    mix *= 0.97 / pk
mix = np.tanh(mix * 1.02) * 0.97

master = os.path.join(tempfile.gettempdir(),
                      f"_vc_master_{os.getpid()}.wav")
with wave.open(master, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())

print(f"film {DUR:.2f}s | song {SL:.1f}s | dialogue {dia_ref:.1f} dB")
print(f"  music in {ENTER:7.2f}s  <- song {inA:6.2f}s")
print(f"  splice   {LEAD_AT-a.xf:7.2f}s  -> song {inB:6.2f}s   (ends {inB+lenB:.1f}/{SL:.1f})")
print(f"  duck: gap {a.db_gap:+.0f} / speech {a.db_under:+.0f} / "
      f"banter {a.db_banter:+.0f} / lead {a.db_lead:+.0f} dB   ({len(QUIET)} banter windows)")

if a.preview:
    os.makedirs(os.path.dirname(a.preview) or ".", exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", master,
                    "-c:a", "libmp3lame", "-b:a", "160k", a.preview], check=True)
    print("  ->", a.preview)
if a.mux:
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.mux, "-i", master,
                    "-map", "0:v", "-c:v", "copy", "-map", "1:a", "-c:a", "aac",
                    "-b:a", "192k", "-movflags", "+faststart", a.out], check=True)
    print("  ->", a.out)

try:
    os.unlink(master)
except OSError:
    pass
