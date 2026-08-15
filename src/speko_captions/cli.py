"""speko-captions CLI.

    speko-captions transcribe video.mp4           # Speko transcript + word timings
    speko-captions render video.mp4 -c cfg.json   # full pipeline -> out/video.captioned.mp4
    speko-captions frames out/video.captioned.mp4 -t 1,8,15
"""

import argparse
import difflib
import json
import sys
from pathlib import Path

from . import align, assgen, render, transcribe
from .config import load_config


def _say(msg: str) -> None:
    print(f"[speko-captions] {msg}", file=sys.stderr)


def _norm_tokens(text: str) -> list[str]:
    return [t.strip(".,?!\"'").lower() for t in text.split() if t.strip(".,?!\"'")]


def cmd_transcribe(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    video = Path(args.video)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    _say("extracting audio")
    audio = transcribe.extract_audio(video)
    _say("transcribing via Speko /v1/transcribe")
    result = transcribe.transcribe(audio, language=cfg["stt"]["language"], pin=cfg["stt"]["pin"])
    _say(f"transcript from {result.get('provider')}/{result.get('model')}")
    (out_dir / f"{video.stem}.transcript.txt").write_text(result["text"] + "\n")
    (out_dir / f"{video.stem}.transcript.json").write_text(json.dumps(result, indent=1))

    _say(f"aligning word timings (faster-whisper {cfg['align']['model']})")
    words = align.word_timings(video, model=cfg["align"]["model"])
    duration = render.probe(video)["duration"]
    gap_from = align.coverage_gap(words, duration)
    if gap_from is not None:
        _say(f"alignment stopped early; re-aligning tail from {gap_from:.1f}s")
        words = align.merge_tail(words, align.word_timings_tail(video, gap_from,
                                                               model=cfg["align"]["model"]))
    # Project the Speko transcript (text truth) onto the aligner's timings:
    # captions always show the API text, never the aligner's mishears.
    speko_tokens = _norm_tokens(result["text"])
    whisper_tokens = _norm_tokens(" ".join(w["w"] for w in words))
    ratio = difflib.SequenceMatcher(None, speko_tokens, whisper_tokens).ratio()
    _say(f"aligner/transcript agreement before projection: {ratio:.0%}")
    words = assgen.project_transcript(result["text"], words)
    (out_dir / f"{video.stem}.words.json").write_text(json.dumps(words, indent=1))
    if ratio < 0.75:
        _say("heavy drift: spot-check words.json timings; fix any API-text"
             ' errors (rare) with config "overrides"')
    print(result["text"])
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    video = Path(args.video)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    words_path = out_dir / f"{video.stem}.words.json"
    if not words_path.exists():
        rc = cmd_transcribe(args)
        if rc != 0:
            return rc
    words = json.loads(words_path.read_text())
    words = assgen.apply_overrides(words, cfg["overrides"], cfg["filler_strip"])

    duration = render.probe(video)["duration"]
    ass_text = assgen.build_ass(words, cfg, duration)
    ass_path = out_dir / f"{video.stem}.ass"
    ass_path.write_text(ass_text)
    _say(f"captions -> {ass_path}")

    out_path = out_dir / f"{video.stem}.captioned.mp4"
    _say("rendering (ffmpeg: upscale + burn + loudness normalize)")
    render.render(video, ass_path, cfg, out_path)
    _say(f"done -> {out_path}")

    times = [1.0, duration / 2, max(0.5, duration - 2)]
    frames = render.extract_frames(out_path, times, out_dir / "qa")
    _say("QA frames: " + ", ".join(str(f) for f in frames))
    print(out_path)
    return 0


def cmd_frames(args: argparse.Namespace) -> int:
    times = [float(t) for t in args.times.split(",")]
    frames = render.extract_frames(args.video, times, args.out)
    for f in frames:
        print(f)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="speko-captions",
                                 description="Word-level karaoke captions for talking videos.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("transcribe", help="Speko transcript + word timings")
    p.add_argument("video")
    p.add_argument("-c", "--config", default=None)
    p.add_argument("-o", "--out", default="out")
    p.set_defaults(fn=cmd_transcribe)

    p = sub.add_parser("render", help="full pipeline: transcribe, caption, render")
    p.add_argument("video")
    p.add_argument("-c", "--config", default=None)
    p.add_argument("-o", "--out", default="out")
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("frames", help="extract QA frames from a render")
    p.add_argument("video")
    p.add_argument("-t", "--times", default="1,5,10")
    p.add_argument("-o", "--out", default="out/qa")
    p.set_defaults(fn=cmd_frames)

    args = ap.parse_args()
    try:
        return args.fn(args)
    except transcribe.SpekoError as e:
        _say(str(e))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
