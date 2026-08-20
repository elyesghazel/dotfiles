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
| `ride` | vehicle, wind, engine | `highpass=f=90, loudnorm=I=-24` |

The high-pass is doing most of the work — wind is almost entirely below 110 Hz, and removing
it makes speech dramatically clearer. Keep `afftdn` gentle (`nf=-25`); harder settings sound
underwater.

Non-speech material is deliberately normalised *quieter*. It is texture, not content.

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
