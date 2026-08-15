---
name: speko-captions
description: Turn a talking video into a social-ready 9:16 clip with word-level karaoke captions. Use when the user drops a video and asks to caption it, make it TikTok/Reels/Shorts-ready, add burned-in subtitles, or prep a clip for social. Pipeline is Speko API transcription + faster-whisper word timings + ffmpeg render, with a mandatory frame-QA loop.
---

# Speko Captions (agent workflow)

You drive this pipeline with the CLI. Do not read the engine source; the
commands and artifacts below are the interface. Requirements: `ffmpeg` on
PATH, `uv`, and `SPEKO_API_KEY` set (keys at https://speko.ai).

## Pipeline

### 1. Probe

```bash
ffprobe -v error -show_entries stream=width,height:format=duration -of csv <video>
```

Note the duration. Vertical sources render best; landscape sources still work
(they upscale to 1080x1920 letterboxed by the caption safe areas).

### 2. Transcribe + align

```bash
uv run speko-captions transcribe <video> -o out
```

Artifacts in `out/`: `<stem>.transcript.txt` (Speko API text - this is the
transcript truth), `<stem>.transcript.json` (provider/model that ran it),
`<stem>.words.json` (word timings from the local aligner).

### 3. Reconcile (agent judgment)

Read `transcript.txt` and `words.json`. Where the aligner's words differ from
the Speko transcript (names, jargon, product terms), write `overrides` in the
config so the burned captions match the Speko text. Where the speaker false-starts
or drops filler ("like", "you know"), add the word start times to
`filler_strip`. The CLI prints an agreement score; below 90% means do this
carefully.

### 4. Configure

Write `<video>.config.json`. Schema and defaults: `src/speko_captions/config.py`
(documented in README). Minimum worth setting:

- `hook.text`: 5-8 word on-screen hook, `\N` for a line break, shown ~2.2s.
- `tags`: speaker name lower-thirds with start/duration.
- `overrides` + `filler_strip` from step 3.
- `caption.active_color` if the default does not fit the footage.

### 5. Render

```bash
uv run speko-captions render <video> -c <video>.config.json -o out
```

Output: `out/<stem>.captioned.mp4` (1080x1920, H.264, AAC, -14 LUFS,
faststart) plus QA frames in `out/qa/`.

### 6. QA loop (MANDATORY - do not skip)

Spawn a subagent to review the QA frames with fresh eyes. Give it the frames
in `out/qa/` and this checklist; render again after every fix until it passes:

- Captions inside the safe area (block center ~y=1150 on 1920): not over a
  face, not under platform UI.
- Active-word highlight lands on the word being spoken (spot-check 3 frames
  against `words.json` times).
- No two caption pages visible at once; no orphaned filler words headlining
  a page ("LIKE" alone = fix `filler_strip`).
- Hook readable, inside side margins, gone by ~2.5s.
- Tags appear only while that person speaks.
- Names and product terms match the Speko transcript exactly.

Then listen once end to end (or extract audio peaks) to confirm speech is
intelligible and the ending is not cut mid-word.

### 7. Deliver

Hand back the captioned mp4 path, the transcript, and the QA frames. Post
copy is out of scope for this skill; captions belong to the video.

## Failure modes

- `SPEKO_API_KEY is not set`: get a key at https://speko.ai, export it.
- Empty transcript: retry; if a pinned provider fails, drop `stt.pin` and let
  the router route.
- Aligner stops early on crosstalk: the CLI re-aligns the tail automatically;
  verify the last words of `words.json` reach the clip end.
- Font missing: the repo bundles Geist in `fonts/`; pass nothing, it is the
  default `fontsdir`.
