# Grades and audio treatment

## Grade profiles (`grade` in edl.json)

Action-cam footage is already contrasty. Stay light-handed — the job is matching shots to
each other, not "colour grading".

| profile | for | ffmpeg |
|---|---|---|
| `base` | normal daylight | `eq=contrast=1.06:saturation=1.10:gamma=1.02` |
| `hot` | blown-out, shooting into sun | `eq=contrast=1.10:saturation=1.12:gamma=0.90:brightness=-0.045` |
| `shade` | dim forest, overcast | `eq=contrast=1.05:saturation=1.12:gamma=1.10:brightness=0.020` |
| `dark` | caves, interiors | `eq=contrast=1.12:saturation=1.05:gamma=1.30:brightness=0.045` |
| `golden` | low sun | `...,colorbalance=rm=0.04:gh=0.01:bs=-0.03` |
| `dusk` | sunset, blue hour | `...,colorbalance=rm=0.05:bs=-0.04` |

## Audio profiles (`aud` in edl.json)

Action-cam audio arrives wildly inconsistent. Measure first:

```sh
ffmpeg -v info -i clip.mp4 -af volumedetect -f null /dev/null 2>&1 | grep _volume
```

Typical: a talking-head clip sits near −25 dB mean, the same camera on a moving vehicle near
−15 dB. That 10 dB gap is wind and engine, not content, and it must be removed or the ride
section will blow the viewer's ears off.

| profile | for | chain |
|---|---|---|
| `voice` | anything with speech | `highpass=f=110, afftdn=nf=-25, acompressor=threshold=-20dB:ratio=3:attack=15:release=250:makeup=2, loudnorm=I=-16:TP=-1.5:LRA=11` |
| `amb` | scenery, no speech | `highpass=f=100, loudnorm=I=-22` |
| `ride` | vehicle as texture under something else | `highpass=f=90, loudnorm=I=-24` |
| `engine` | the engine **is** the content | `highpass=f=55, treble=g=-5:f=7000:q=0.7, loudnorm=I=-14:TP=-1:LRA=9` |

The high-pass is doing most of the work — wind is almost entirely below 110 Hz, and removing
it makes speech dramatically clearer. Keep `afftdn` gentle (`nf=-25`); harder settings sound
underwater.

Non-speech material is deliberately normalised *quieter* — it is texture, not content.
`engine` is the exception: for an engine-sound piece it is the subject, so it is normalised
loud (≈ −14 LUFS, what Instagram/YouTube normalise to) and the high-pass sits at 55 Hz rather
than 90, because a 2-stroke firing frequency drops to ~50 Hz off idle and a 90 Hz filter would
eat the fundamental.

## Finding usable engine audio

Wind and engine separate cleanly in the spectrum, so pick shots by measurement, not by guessing:

- **Spectral flatness** in 70–3000 Hz — low = tonal = engine, high = broadband = wind.
- **Sub-60 Hz share** — wind buffeting and handling noise live here.
- **Above 6 kHz share** — wind hiss.
- **Acceleration pulls**: a 2-stroke fires once per revolution, so the spectral fundamental
  *is* rpm. Track it (harmonic product spectrum handles a missing fundamental) and look for
  monotone rises — that climbing note is the shot the whole piece exists for.

Then confirm by eye: `showspectrumpic` on the candidates. Real engine shows crisp harmonic
stacks or rising diagonals; wind is a formless red wash. Beware octave errors in the tracker —
the relative rise is trustworthy, the absolute rpm is not.

### Check you have the right machine

**Sub-60 Hz share also tells combustion from electric.** A piston engine fires once (two-stroke)
or once per two revolutions (four-stroke) per cylinder, and that pulse puts real energy below
60 Hz. An electric motor has no such pulse — just a tonal whine — so its sub-60 Hz share sits
**20–35 dB lower**:

```
2-stroke clips     sub-60Hz  -4 to -6 dB
electric (Stark)   sub-60Hz  -30 to -40 dB
```

This bit once: two clips from the same evening measured as having *unusually clean* low end and
scored top of the wind ranking. They were not clean — they were a different, electric bike, and
one got cut into a video titled "raw 2 stroke". Plot the ratio per clip **and over time within
each clip** (riders swap bikes mid-session), and sanity-check against the cockpit: crop the
lower third of a frame and look at the bars.

If the piece is about a specific machine, verify which machine is in every shot before cutting.
The audio metric that looks like "best quality" may just be the wrong vehicle.

## Ducking depths

Referenced to the measured dialogue level, not absolute numbers — normalise the song to a
known RMS first, otherwise its own dynamics make any fixed gain a lottery.

| where | relative to dialogue | why |
|---|---|---|
| gap, no speech | −2 dB | present, still not competing |
| under speech | −14 dB | audible bed, words on top |
| **banter / punchline** | **−23 dB** | the joke lands dry |
| vehicle / montage | +2 dB | music leads |

Ramp between levels over ~1.1 s. Instant changes are audible as pumping.

List the extra-duck windows in a `banter.json` keyed by source clip and source timecode;
`speechmap.py` maps them onto film time so they survive re-cuts.

## Clip-edge fades

With no music, natural audio is the whole soundtrack and hard joins click. Fade every clip's
audio in and out over at least 5 frames, and over the dissolve length where there is one.
`timeline.py` emits `fadeIn`/`fadeOut` per clip for exactly this.
