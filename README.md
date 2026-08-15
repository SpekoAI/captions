# speko-captions

[![CI](https://github.com/SpekoAI/captions/actions/workflows/ci.yml/badge.svg)](https://github.com/SpekoAI/captions/actions/workflows/ci.yml)

Turn a talking video into a social-ready 9:16 clip with word-level karaoke
captions. One CLI, three stages: transcription by the
[Speko API](https://speko.ai), word timings by faster-whisper (local), render
by ffmpeg. Built agent-first: `SKILL.md` makes any coding agent a video
editor with a review loop.

Landing page: [captions.speko.ai](https://captions.speko.ai)

## Quickstart

macOS and Linux (Windows: use WSL).

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
  return. The Speko transcript is then projected onto those timings, so the
  burned captions always show the API text, never the aligner's mishears.
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
  "overrides": [{"from": ["speco"], "to": ["Speko"]}],
  "caption": {"active_color": "#38BDF8", "max_words": 4},
  "case_keep": ["IDEs", "iMessage"]
}
```

Every key, with its default:

| Key | Default | Meaning |
|---|---|---|
| `caption.font` | `"Geist Black"` | caption font (bundled in `fonts/`) |
| `caption.size` | `88` | caption font size on the 1080x1920 canvas |
| `caption.y` | `1150` | caption block center; clears TikTok/Reels/Shorts UI |
| `caption.text_color` | `"#FFFFFF"` | inactive word color |
| `caption.active_color` | `"#38BDF8"` | spoken-word highlight color |
| `caption.outline` / `caption.shadow` | `7` / `2` | black outline and shadow weight |
| `caption.max_words` / `caption.max_chars` | `4` / `18` | page size caps |
| `caption.gap_break` | `0.55` | silence (s) that forces a new page |
| `caption.case` | `"upper"` | `upper`, `keep`, or `lower` |
| `caption.pop` | `1.08` | active-word scale; `1.0` disables |
| `hook` | `null` | `{"text", "seconds", "y", "size"}`; `\N` breaks lines |
| `tags` | `[]` | `{"text", "subtext", "start", "dur"}` lower-thirds |
| `filler_strip` | `[]` | start times (s) of words to hide from display |
| `overrides` | `[]` | `{"from": [...], "to": [...]}` word substitutions; every occurrence, any length |
| `case_keep` | `[]` | words whose casing survives the case transform |
| `audio.target_i` / `target_tp` / `target_lra` | `-14` / `-1.5` / `11` | loudness normalization targets |
| `audio.highpass` / `denoise` / `presence_eq` | `80` / `true` / `true` | speech cleanup chain |
| `audio.fade_out` / `video.fade_out` | `0.25` / `0.29` | end fades (s) |
| `video.width` / `height` / `crf` / `sharpen` | `1080` / `1920` / `18` / `true` | export geometry and quality |
| `stt.language` / `stt.pin` | `"en"` / `null` | transcription intent; pin forces one STT lane |
| `align.model` | `"small.en"` | faster-whisper model for timings |

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
