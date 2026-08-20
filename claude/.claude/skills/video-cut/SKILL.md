---
name: video-cut
description: Cut raw camera footage into a finished film — GoPro/action-cam clips, vlogs, hiking or riding footage, travel edits, supercuts. Use when the user says "cut my vlog", "edit this footage", "make a video from these clips", "add music/titles/transitions to a video", or points at a folder of clips and wants something watchable. Covers surveying and *watching* footage, transcript-driven cutting so speech is never chopped mid-sentence, per-clip grading, audio levelling, Remotion titles/cards, and a music bed that is mixed outside the render so it can be re-tuned in seconds.
---

# Cutting footage into a film

An edit is decisions, not encoding. The pipeline below exists so that every decision lives
in one small file (`edl.json`) and everything else is regenerated from it. Change a cut
point, re-run, done.

## The rule that matters most

**Never cut someone mid-sentence.** This is the single most common complaint and it is
entirely avoidable: transcribe first, cut on segment boundaries. Round numbers like "20.0s"
are always wrong. If the footage has speech, `transcribe.py` runs *before* you write the EDL,
not after the user complains.

Dropping whole sentences is fine editing. Truncating one is not.

## Order of work

1. **Survey** — `survey.py <dir>` prints duration/res/fps/audio per clip and writes contact
   sheets. Read the sheets *as images*. You cannot edit footage you have not looked at.
2. **Transcribe** — `transcribe.py <dir>` → `work/transcript.json` (faster-whisper, VAD on).
   Gives sentence boundaries *and* tells you what is actually said, so you can keep the
   informative and funny bits and drop rambling.
3. **Write `edl.json`** — the edit. One object per shot; in-points snapped to transcript
   segments. This is the only file you hand-author.
4. **`trim.py`** — cuts, grades and levels each shot into `public/clips/`.
5. **`timeline.py`** — frame-accurate starts, dissolve lengths → `src/timeline.json`.
6. **`speechmap.py`** — maps the transcript onto *film* time → `speech.json` (where music
   must duck, and where it may breathe).
7. **Render picture** with Remotion.
8. **`score.py`** — builds the music bed and muxes with `-c:v copy`.

Steps 4–6 and 8 are seconds. Only step 7 is slow, which is why music is not in it.

## edl.json

```json
{"id":"01_intro","src":"GX010961","in":0.00,"dur":21.14,
 "act":"arrival","grade":"base","aud":"voice"}
{"id":"06_rules","src":"GX010966","in":34.70,"dur":12.18,
 "act":"cliff","grade":"base","aud":"voice","diss":true}
```

| field | |
|---|---|
| `id` | orders the film, names the trimmed file. Prefix with a number. |
| `src` | source filename without extension |
| `in` / `dur` | seconds. **Snap `in` and `in+dur` to transcript segment boundaries.** |
| `act` | groups shots; an act change triggers a dissolve and a chapter card |
| `grade` / `aud` | look and audio treatment — `references/audio.md` |
| `diss` | **force a dissolve into this shot** even though the act did not change |
| `dir` | optional: absolute path, or a folder beside the footage dir, for misfiled clips |

**`diss` matters more than it looks.** Dissolves are derived from act changes, which is right
most of the time. But two shots in the same act still need one when the picture jumps — a
jump cut inside one source clip, or a hard change of location or camera position within an
act. Forget it and the film hard-cuts where it should dissolve; every downstream frame number
shifts, and `speech.json` shifts with it, so the music ducks in the wrong places.

Rule of thumb: if consecutive shots share an `act` but the viewer would notice a jump, set
`"diss": true`.

## Environment

| var / flag | |
|---|---|
| `GOPRO_SRC` | footage directory for `trim.py` (or `--src`) |
| `VLOG_MUSIC` | song path for `score.py` (or `--music`) |
| `trim.py --only a,b` | rebuild just these shots after an EDL tweak |
| `score.py --preview PATH` | write the audio master to an mp3 (takes a path) |
| `score.py --enter S` / `--lead-at S` | override where music enters / takes the lead |

## Things that will bite you

**Memory, not CPU, caps the render.** Remotion runs one headless Chrome per concurrent
frame at roughly 0.8–1.4 GB at 1080p. Exceed RAM and the kernel kills it — the render dies
with **exit 144** and no useful error. Check `dmesg | grep -i oom`. Set concurrency from
*free RAM ÷ 1.2 GB*, not from core count.

**GoPro metadata breaks `json.load`.** Raw control characters in the tags; use
`json.loads(..., strict=False)`.

**Proxy transcodes have no GPMF.** No GPS, speed or altitude, and often no `creation_time`.
Order from filename numbering; get location from what is on screen. Say so when you label
places — never present an inference as fact.

**Camera clocks lie.** Folder names derived from clip timestamps are frequently years off.
Ask the user the real date before putting it on a title card.

**`np.convolve` is O(n·k).** A 1-second smoothing kernel at 48 kHz over a 3-minute track is
~5·10¹¹ operations. Use the repeated box filter in `score.py` — O(n), and it turns minutes
into seconds.

## Music

**Never source copyrighted music yourself.** Do not pull it from streaming rips or torrents.
If the user names a track, ask them to supply a file they own — then do the editing work,
which is the part that has value.

Arrange it, do not just lay it under:

- Enter on a natural gap, usually after the opening monologue.
- **Cut the song so its shape matches the film's.** Splicing a verse out during a ducked
  stretch lets the final chorus land on the emotional peak and the song's own fade-out land
  on the fade to black. Snap splices to an onset.
- Duck from the transcript, not a sidechain — you know exactly where the words are.
- Duck *harder* under jokes and punchlines. A gag lands dry.

## Previews are the feedback loop

A 25-minute render is a terrible way to answer "is the music too loud". Give the user, in
descending order of speed:

1. **Audio-only MP3** (~4 MB) — settles every audio question in seconds on a phone.
2. **Rough cut** — `ffmpeg concat -c copy` of the trimmed clips. No titles or dissolves.
   Costs nothing. *Say clearly that the visuals are deliberately absent*, or they will
   report the cards as missing.
3. **Full render** — last.

Serve them over a **localhost or tailnet-bound** HTTP server. Never bind `0.0.0.0` on a host
without a firewall.

## Reference

- `references/pipeline.md` — the scripts in detail, EDL fields, dissolve rules
- `references/audio.md` — grade and audio profiles, levels, ducking depths
