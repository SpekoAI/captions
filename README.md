# speko-captions

[![CI](https://github.com/SpekoAI/captions/actions/workflows/ci.yml/badge.svg)](https://github.com/SpekoAI/captions/actions/workflows/ci.yml)

Turn a talking video into a social-ready 9:16 clip with word-level karaoke
captions. One CLI, three stages: transcription by the
[Speko API](https://speko.ai), word timings by faster-whisper (local), render
by ffmpeg. Built agent-first: `SKILL.md` makes any coding agent a video
editor with a review loop.

Landing page: [captions.speko.ai](https://captions.speko.ai)

## Quickstart

1. Install ffmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux).
2. Install [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Get a Speko API key at [speko.ai](https://speko.ai).
4. `export SPEKO_API_KEY=sk_...`
5. `git clone https://github.com/SpekoAI/captions && cd captions && uv sync`
6. `uv run speko-captions render your-video.mp4`

Output: `out/your-video.captioned.mp4` (1080x1920, H.264, AAC, -14 LUFS,
faststart) plus QA frames in `out/qa/`. No video? `uv run python
samples/make_sample.py` generates one, voiced by the same Speko API.

## What it does

- **Transcript truth from one API.** Audio goes to Speko `/v1/transcribe`;
  the router benchmarks STT providers continuously and picks the lane per
  request. Pin one with `stt.pin` if you must.
- **Word-level timing locally.** faster-whisper supplies timestamps only -
  the karaoke highlight needs per-word times, which batch STT APIs do not
  return. It never overrides the Speko transcript text; you reconcile
  differences with config `overrides`.
- **Editor-grade captions.** Phrase-aware pages (max words, max chars,
  silence and punctuation breaks), active-word color + scale pop, filler-word
  stripping, hook text, speaker tags, safe-zone placement for TikTok, Reels,
  and Shorts UI.
- **Clean audio.** Highpass, denoise, presence EQ, two-pass loudness
  normalization to -14 LUFS with true-peak ceiling.

## Config

Everything an editor touches lives in one JSON file per video:

```json
{
  "hook": {"text": "MY AGENTS CALL ME\\NON THE PHONE", "seconds": 2.2},
  "tags": [{"text": "JANE DOE", "subtext": "CTO, EXAMPLE", "start": 12.0, "dur": 3.0}],
  "filler_strip": [0.98, 2.14],
  "overrides": [{"from": ["cloud", "code"], "to": ["Claude", "Code"]}],
  "caption": {"active_color": "#38BDF8", "max_words": 4},
  "case_keep": ["IDEs", "iMessage"]
}
```

Full schema with defaults and comments: `src/speko_captions/config.py`.

## Agent-first

`SKILL.md` is a drop-in [Claude Code](https://claude.com/claude-code) skill.
It runs the same CLI, then adds the part a CLI cannot do: judgment. The agent
reconciles aligner mishears against the Speko transcript, writes the config,
and runs a mandatory subagent QA loop over extracted frames (placement,
sync, orphaned fillers, safe zones) before calling a render done.

```bash
mkdir -p ~/.claude/skills/speko-captions
cp SKILL.md ~/.claude/skills/speko-captions/
```

## Commands

| Command | Does |
|---|---|
| `speko-captions transcribe <video>` | Speko transcript + word timings into `out/` |
| `speko-captions render <video> -c cfg.json` | full pipeline to `out/<stem>.captioned.mp4` |
| `speko-captions frames <video> -t 1,8,15` | extract QA frames |

## Development

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
```

Tests run without network or ffmpeg; caption generation is a pure function
with a golden-file test.

## License

MIT. Geist font by Vercel, bundled under the SIL Open Font License 1.1
(`fonts/OFL.txt`).
