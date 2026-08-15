---
name: speko-captions
description: Turn a talking video into a social-ready 9:16 clip with word-level karaoke captions. Use when the user drops a video and asks to caption it, make it TikTok/Reels/Shorts-ready, add burned-in subtitles, or prep a clip for social. Pipeline is Speko API transcription + faster-whisper word timings + ffmpeg render, with a mandatory frame-QA loop.
---

# Speko Captions (agent workflow)

You drive this pipeline with the CLI. Do not read the engine source; the
commands and artifacts below are the interface. Requirements: `ffmpeg` on
PATH, `uv`, and `SPEKO_API_KEY` set (keys at https://speko.ai).

## Pipeline

### 0. Get the tool

All commands run from the repo root:

```bash
git clone https://github.com/SpekoAI/captions && cd captions && uv sync
```

If the repo is already cloned, `cd` into it. Videos elsewhere on disk are
fine; pass absolute paths.

### 1. Probe

```bash
ffprobe -v error -show_entries stream=width,height:format=duration -of csv <video>
```

Note the duration. Vertical sources render best; landscape sources still
work (they upscale to 1080x1920).

### 2. Transcribe + align

```bash
uv run speko-captions transcribe <video> -o out
```

Artifacts in `out/`: `<stem>.transcript.txt` (Speko API text - the
transcript truth), `<stem>.transcript.json` (provider/model that ran it),
`<stem>.words.json` (per-word timings, already projected onto the Speko
text - captions show the API transcript, not the aligner's hearing).

### 3. Review the words (agent judgment)

Read `transcript.txt` and `words.json`. Two things to author:

- `overrides` fix words that are wrong IN THE API TEXT itself (rare:
  product names, code-switching). Shape, matching, and semantics:

  ```json
  "overrides": [{"from": ["speco"], "to": ["Speko"]}]
  ```

  `from` matches a consecutive run of words in `words.json`
  (case-insensitive, ignoring ,.?! punctuation); every occurrence is
  replaced by `to`, which may be longer or shorter - timing redistributes
  across the matched span.

- `filler_strip` hides false starts and fillers from display (audio is
  untouched). List the exact `s` start times from `words.json`:

  ```json
  "filler_strip": [0.98, 2.14]
  ```

  Never strip a comparative "like" ("anything like that") or a quotative
  "I'm like" - only dead fillers.

### 4. Configure

Write `<video>.config.json`. The full schema with defaults is in the README
"Config" section. Minimum worth setting:

- `hook.text`: 5-8 word on-screen hook, `\N` for a line break, shown ~2.2s.
- `tags`: speaker name lower-thirds with `start`/`dur` seconds.
- `overrides` + `filler_strip` from step 3.
- `caption.active_color` if the default does not fit the footage.

### 5. Render

```bash
uv run speko-captions render <video> -c <video>.config.json -o out
```

Output: `out/<stem>.captioned.mp4` (1080x1920, H.264, AAC, -14 LUFS,
faststart) plus three QA frames in `out/qa/`.

### 6. QA loop (MANDATORY - do not skip)

Extract extra frames at any timestamps you want to inspect:

```bash
uv run speko-captions frames out/<stem>.captioned.mp4 -t 1,4.5,9 -o out/qa
```

Spawn a subagent to review the frames in `out/qa/` with fresh eyes. Give it
this checklist; re-render after every fix until it passes clean:

- Captions inside the safe area (block center ~y=1150 on 1920): not over a
  face, not under platform UI.
- Active-word highlight lands on the word being spoken (spot-check 3 frames
  against `words.json` times).
- No two caption pages visible at once; no orphaned filler words headlining
  a page ("LIKE" alone = fix `filler_strip`).
- Hook readable, inside side margins, gone by ~2.5s.
- Tags appear only while that person speaks.
- Names and product terms match the transcript exactly.

Then listen once end to end to confirm speech is intelligible and the
ending is not cut mid-word.

### 7. Deliver

Hand back the captioned mp4 path, the transcript, and the QA frames. Post
copy is out of scope for this skill; captions belong to the video.

## Failure modes

- `SPEKO_API_KEY is not set`: get a key at https://speko.ai, export it.
- `the API rejected the key`: the key is wrong or revoked; no retry helps.
- Empty transcript: the CLI already falls back across STT lanes; if all
  fail, retry once, then check api.speko.dev status.
- Aligner stops early on crosstalk: the CLI re-aligns the tail
  automatically; verify the last words of `words.json` reach the clip end.
- `has no audio stream`: the input is a silent video; nothing to caption.
- Windows is unsupported; use WSL.
