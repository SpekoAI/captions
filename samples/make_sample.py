#!/usr/bin/env python3
"""Generate the bundled sample video: voice by Speko /v1/synthesize,
picture by ffmpeg (waveform over the palette). Fully synthetic - no faces,
no consent questions - and it exercises the same API the captioner uses.

    uv run python samples/make_sample.py
"""

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from speko_captions.transcribe import api_credentials

TEXT = ("Speko captions turns any talking video into a social ready clip. "
        "One API transcribes the speech, and ffmpeg burns word level captions. "
        "This voice comes from the same API.")

OUT_DIR = Path(__file__).parent
PCM = OUT_DIR / "sample.pcm"
MP4 = OUT_DIR / "sample.mp4"


def synthesize() -> None:
    base, key = api_credentials()
    body = json.dumps({"text": TEXT, "intent": {"language": "en"}}).encode()
    req = urllib.request.Request(
        base + "/v1/synthesize", data=body, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        ctype = resp.headers.get("Content-Type", "")
        PCM.write_bytes(resp.read())
    if "pcm" not in ctype:
        raise RuntimeError(f"unexpected synthesize content-type: {ctype}")


def compose() -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", str(PCM),
         "-f", "lavfi", "-i", "color=c=0x0e1512:s=1080x1920:r=30",
         "-filter_complex",
         ("[0:a]showwaves=s=960x420:mode=cline:colors=0x2f6ad1[w];"
          "[1:v][w]overlay=(W-w)/2:(H-h)/2:shortest=1,"
          "drawtext=text='speko captions':fontcolor=white:fontsize=64:"
          "x=(w-text_w)/2:y=560"),
         "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", str(MP4)],
        check=True,
    )
    PCM.unlink(missing_ok=True)


if __name__ == "__main__":
    synthesize()
    compose()
    print(MP4)
