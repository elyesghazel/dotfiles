# Hiding something in the frame

Number plates, instrument clusters, faces, house numbers. The instinct is "track it and blur
it". Sometimes that is right. Often a fixed region is the better engineering call, and the
decision should be made on measurement rather than on which sounds more sophisticated.

## Decide with one question

**What is the cost of a single missed frame?**

If the point is to not show a speedometer, a number plate, or someone's face, then one leaked
frame defeats the whole exercise. Reliability beats elegance. A fixed region cannot lose lock.

If the subject is small and the surrounding image matters (a face in a wide landscape), spend
the effort on tracking.

## First, measure the motion

Do not assume from a handful of stills. Sample 20–30 frames spread across the cut, crop the
region of interest, tile them, and *look*.

Two very different situations:

- **Camera rigidly attached to the subject** (bike-mounted cam looking at that bike's dash).
  The subject barely moves in frame — jitter only. A small fixed box works, or trivial tracking.
- **Camera on the operator** (helmet cam looking at the same dash). The subject translates,
  scales, and leaves frame. Measured on a real reel: the cluster ranged across **~10–85% of
  frame width** and was absent in ~25% of frames.

Ask which mount it is. Do not infer it from stills — the two look identical in a still.

## Tracking: what actually goes wrong

`cv2.matchTemplate` with `TM_CCOEFF_NORMED` **returns confident nonsense on textured scenes.**
A real failure, worth internalising:

```
01_open  180f  locked 73.9%  x  79-1589 (±755)   <- "73.9% locked" on a 1920-wide frame
```

73.9% "locked" with a mean score of 0.73, while the match wandered 1650 px across the frame.
The score cannot distinguish the subject from asphalt.

**Never accept a tracking score as evidence.** Plot the track, draw the box on frames, and
look at them. A tracker that reports 0% lost and is wrong is worse than one that admits failure.

Things that make a target hard, all of which applied at once:

- small (a few hundred px wide) and **dark**
- heavy motion blur
- lighting swinging from into-sun to deep shadow
- regularly clipped by the frame edge or occluded

Colour detection is tempting for a saturated target (yellow handlebars). It failed at golden
hour, because **the sunlit grass and warm asphalt were also yellow** — the HSV mask returned
the full frame width. Check the colour is distinctive *in that footage*, not in general.

If tracking is genuinely required: a proper tracker (`cv2.TrackerCSRT`) hand-initialised per
shot and re-initialised on loss, plus a verification pass. Budget real time for the verification.

## The fixed feathered region

```sh
# mask: transparent above FEATHER_TOP, opaque from FULL_FROM down, smoothstep between
python3 - <<'PY'
import numpy as np, cv2
H, W, FEATHER_TOP, FULL_FROM = 1080, 1920, 700, 800
y = np.arange(H, dtype=np.float32)
t = np.clip((y - FEATHER_TOP) / (FULL_FROM - FEATHER_TOP), 0, 1)
s = t * t * (3 - 2 * t)
cv2.imwrite("blurmask.png", np.repeat((s*255).astype(np.uint8)[:, None], W, axis=1))
PY

ffmpeg -nostdin -i in.mp4 -loop 1 -i blurmask.png -filter_complex \
 "[0:v]gblur=sigma=14:steps=3,format=yuva420p[b];[1:v]format=gray[m];\
  [b][m]alphamerge[ba];[0:v][ba]overlay=0:0:shortest=1[v]" \
 -map "[v]" -map 0:a -c:v libx264 -preset medium -crf 20 -c:a copy \
 -movflags +faststart out.mp4
```

- **Copy the audio** (`-c:a copy`). An approved mix should not be re-encoded to hide a dial.
- **Feather.** A hard-edged band reads as a censor bar; a smoothstep ramp reads as depth of
  field, especially over a region that is mostly the vehicle itself.
- Runs in well under a minute for a one-minute 1080p clip, and needs no re-render — so this
  is a post step on the finished picture, never something baked into the composition.

### Calibrate the two numbers by measurement

**Geometry.** Find the extreme position — for a dash, the frame where the operator is looking
down hardest. Overlay a pixel ruler and read it off. Add ~40 px of margin.

**Strength.** Do not guess sigma. Render the *worst-case* frame (subject largest and sharpest)
at several sigmas, stack them, and look:

```
sigma 10  needle angle and odometer already unreadable, bike clearly recognisable
sigma 14  chosen — margin, bike still reads
sigma 22  bike becoming a smear
sigma 36  bike gone; far more than needed
```

Calibrating on the worst case makes every other frame safe, since the subject is smaller there.

## Consider what else is in shot

On the reel above, the speed was the concern — but the **odometer** was equally legible and is
effectively a fingerprint for that specific vehicle. Look at what is actually readable, not
only the thing the user named.
