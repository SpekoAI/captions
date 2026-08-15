"""Transcript truth: POST the audio to the Speko API /v1/transcribe.

The Speko router benchmarks STT providers continuously and picks the lane;
pass stt.pin in the config to force one. Docs: https://docs.speko.dev
"""

import json
import os
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://api.speko.dev"


class SpekoError(RuntimeError):
    pass


def api_credentials() -> tuple[str, str]:
    key = os.environ.get("SPEKO_API_KEY", "")
    if not key:
        raise SpekoError("SPEKO_API_KEY is not set. Get a key at https://speko.ai")
    base = os.environ.get("SPEKO_API_BASE", DEFAULT_BASE).rstrip("/")
    return base, key


def extract_audio(video: str | Path, out_dir: str | Path | None = None) -> Path:
    """Extract mono 16kHz mp3 (the container every STT lane accepts)."""
    out_dir = Path(out_dir) if out_dir else Path(tempfile.mkdtemp(prefix="speko-captions-"))
    out = out_dir / (Path(video).stem + ".16k.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
         "-vn", "-ac", "1", "-ar", "16000", "-b:a", "96k", str(out)],
        check=True,
    )
    return out


def _parse_sse_done(body: str) -> dict | None:
    done = None
    for event in body.split("\n\n"):
        if "event: done" in event:
            for line in event.splitlines():
                if line.startswith("data: "):
                    done = json.loads(line[6:])
    return done


# Fallback pins tried when the routed lane errors or returns empty text.
FALLBACK_PINS = ["alibaba:qwen3-asr-flash", "openai:whisper-1"]


def _attempt(base: str, key: str, data: bytes, language: str, pin: str | None,
             timeout: int) -> dict | Exception:
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/octet-stream",
        "X-Speko-Intent": json.dumps({"language": language, "optimizeFor": "accuracy"}),
    }
    if pin:
        headers["X-Speko-Constraints"] = json.dumps({"allowedProviders": {"stt": [pin]}})
    try:
        req = urllib.request.Request(base + "/v1/transcribe", data=data,
                                     headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
        done = _parse_sse_done(body)
        if done and done.get("text", "").strip():
            return done
        return SpekoError(f"empty transcript from lane pin={pin}: {body[:200]}")
    except Exception as e:  # noqa: BLE001 - network layer; caller decides
        return e


def transcribe(audio: str | Path, language: str = "en", pin: str | None = None,
               retries: int = 2, timeout: int = 300) -> dict:
    """Returns the API's done frame: {"text", "provider", "model", ...}.

    Lane order: the config pin (or the router's own choice when unpinned),
    then FALLBACK_PINS. A lane that errors or returns empty text is skipped.
    """
    base, key = api_credentials()
    data = Path(audio).read_bytes()

    lanes: list[str | None] = [pin]
    lanes += [p for p in FALLBACK_PINS if p != pin]
    errors: list[str] = []
    for lane in lanes:
        for attempt in range(retries):
            result = _attempt(base, key, data, language, lane, timeout)
            if isinstance(result, dict):
                return result
            errors.append(f"pin={lane} attempt={attempt}: {result}")
            time.sleep(3 * (attempt + 1))
    raise SpekoError("/v1/transcribe failed on all lanes:\n  " + "\n  ".join(errors))
