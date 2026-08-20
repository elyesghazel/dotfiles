# Pipeline detail

## Layout

```
project/
├── edl.json           the edit — the only hand-authored file
├── banter.json        optional: windows where music ducks harder
├── work/
│   └── transcript.json
├── public/clips/      trimmed, graded, levelled shots
├── src/
│   ├── timeline.json  generated: frame-accurate starts + dissolves
│   ├── theme.ts       place names, chapter cards
│   ├── Vlog.tsx       the composition
│   ├── Titles.tsx     title card, chapter cards, end card, progress
│   └── Grain.tsx      grain + vignette
├── speech.json        generated: speech + duck windows in FILM time
└── out/
```

## Scripts

| script | in | out |
|---|---|---|
| `survey.py <dir>` | footage dir | table + contact sheets |
| `transcribe.py <dir>` | footage dir | `work/transcript.json` |
| `trim.py` | `edl.json` | `public/clips/*.mp4` |
| `timeline.py` | `edl.json` | `src/timeline.json` |
| `speechmap.py` | transcript + timeline | `speech.json` |
| `score.py` | song + `speech.json` | audio master, or muxed film |

## Dissolves

Hard cuts inside an act, ~20-frame dissolves at act boundaries and wherever the EDL sets
`"diss": true`. Dissolving every join is a tell of an unedited edit.

`timeline.py` dissolves into shot *i* when `edl[i].act != edl[i-1].act`, **or** when
`edl[i].diss` is true. The second case covers jump cuts inside one source clip and hard
position changes within an act — cases the act field cannot see. A missing `diss` is not a
cosmetic error: it removes 20 frames, shifting every later `start`, and `speech.json` is
computed from those starts, so the music ends up ducking against the wrong timecodes.

After editing an EDL, re-run `timeline.py` **and** `speechmap.py`. They are seconds; skipping
the second one is a silent desync.

`timeline.py` overlaps sequences by the dissolve length, so total frames =
`sum(durations) − sum(dissolves)`. The incoming clip fades up on top of the outgoing one,
which requires later clips to be later in the DOM.

## Contact sheets

```sh
ffmpeg -i clip.mp4 -vf "fps=1/2,scale=440:-2,tile=5x8" -frames:v 1 sheet.jpg
```

One frame every 2 s. Read them as images and write down what is in each clip — the story,
the hero shots, the dead weight. This is the step that makes the edit good; skipping it
produces a technically correct film that is about nothing.

## Transcript-driven cutting

`transcript.json` holds per-clip `{s, e, t}` segments. Every EDL in/out should coincide with
one. To drop rambling, drop *whole* segments and let the picture jump-cut — cover it with a
short dissolve. Keep:

- anything stating what is happening, where, or how far is left
- anything funny
- the payoff line at a destination

Drop repetition and filler. Check with the user before dropping something that might be a
favourite — jokes are not always where you expect.

## Rendering

```sh
npx remotion render src/index.ts Vlog out/film.mp4 \
  --codec=h264 --crf=20 --concurrency=<free_GB / 1.2> --gl=angle
```

- **CRF 20 is plenty** for camera proxies. CRF 18 on a 12 Mb/s source produced 28 Mb/s of
  output — pure waste. Added film grain also costs real bitrate.
- `--gl=angle` uses the GPU; `swangle` is the software fallback for headless boxes.
- `--hardware-acceleration` affects only the encoder — a few percent. Not the win.
- Drop `premountFor` if memory is tight; it holds extra decoders open.

Smoke-test one still (`npx remotion still ... --frame=N`) before committing to a long render.

## Verifying the result

Do not trust that it worked — check the finished file:

```sh
ffprobe -v error -show_entries format=duration,bit_rate -of default=nw=1 out/film.mp4
ffmpeg -v info -i out/film.mp4 -af volumedetect -f null /dev/null 2>&1 | grep _volume
```

Then pull frames at the title, each chapter card and the end, tile them, and *look*.
