"""ffmpeg rendering: upscale to 9:16, burn captions, clean and normalize audio."""

import json
import re
import subprocess
from pathlib import Path


def _fonts_dir() -> Path:
    packaged = Path(__file__).resolve().parent / "fonts"   # wheel/uvx install
    if packaged.is_dir():
        return packaged
    checkout = Path(__file__).resolve().parents[2] / "fonts"  # repo checkout
    if checkout.is_dir():
        return checkout
    raise RuntimeError(
        "bundled fonts directory not found; reinstall speko-captions or pass fonts_dir"
    )


def escape_filter_path(path: str) -> str:
    """Escape a path for use as an option value inside an ffmpeg filtergraph.

    Two parser levels: the option value first (backslash, colon, quote), then
    the filtergraph itself (backslash, comma, semicolon, brackets, quote).
    """
    s = str(path)
    s = s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    s = (s.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
         .replace("[", "\\[").replace("]", "\\]").replace("'", "\\'"))
    return s


def probe(video: str | Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=width,height,codec_type", "-of", "json", str(video)],
        check=True, capture_output=True, text=True,
    ).stdout
    data = json.loads(out)
    return {"duration": float(data["format"]["duration"])}


def _audio_chain(cfg: dict) -> str:
    a = cfg["audio"]
    parts = [f"highpass=f={a['highpass']}"]
    if a["denoise"]:
        parts.append("afftdn=nf=-28:nr=12")
    if a["presence_eq"]:
        parts.append("equalizer=f=2500:t=q:w=1:g=2")
    return ",".join(parts)


def measure_loudness(video: str | Path, cfg: dict) -> dict:
    a = cfg["audio"]
    af = (_audio_chain(cfg) +
          f",loudnorm=I={a['target_i']}:TP={a['target_tp']}:LRA={a['target_lra']}:print_format=json")
    out = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-af", af, "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stderr
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", out, re.DOTALL)
    if not m:
        raise RuntimeError("loudnorm measurement not found in ffmpeg output")
    return json.loads(m.group(0))


def render(video: str | Path, ass_path: str | Path, cfg: dict, out_path: str | Path,
           fonts_dir: str | Path | None = None) -> Path:
    v = cfg["video"]
    a = cfg["audio"]
    fonts = str(fonts_dir) if fonts_dir else str(_fonts_dir())
    dur = probe(video)["duration"]
    meas = measure_loudness(video, cfg)

    vf = [f"scale={v['width']}:{v['height']}:flags=lanczos"]
    if v["sharpen"]:
        vf.append("unsharp=5:5:0.35:5:5:0.0")
    vf.append(
        f"subtitles=filename={escape_filter_path(ass_path)}"
        f":fontsdir={escape_filter_path(fonts)}"
    )
    if v["fade_out"] > 0:
        vf.append(f"fade=t=out:st={max(0, dur - v['fade_out']):.2f}:d={v['fade_out']}")

    af = (
        _audio_chain(cfg)
        + f",loudnorm=I={a['target_i']}:TP={a['target_tp']}:LRA={a['target_lra']}"
        + f":measured_I={meas['input_i']}:measured_TP={meas['input_tp']}"
        + f":measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}"
        + f":offset={meas['target_offset']}:linear=true"
    )
    if a["fade_out"] > 0:
        af += f",afade=t=out:st={max(0, dur - a['fade_out']):.2f}:d={a['fade_out']}"

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
         "-vf", ",".join(vf), "-af", af,
         "-c:v", "libx264", "-crf", str(v["crf"]), "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", str(out_path)],
        check=True,
    )
    return out_path


def extract_frames(video: str | Path, times: list[float], out_dir: str | Path,
                   width: int = 540) -> list[Path]:
    """QA frames for the agent (or human) to review caption placement."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for t in times:
        f = out_dir / f"frame-{t:05.1f}s.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(video),
             "-frames:v", "1", "-vf", f"scale={width}:-1", str(f)],
            check=True,
        )
        frames.append(f)
    return frames
