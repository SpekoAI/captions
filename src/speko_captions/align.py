"""Word-level timings via faster-whisper (local, CPU).

This provides ONLY the per-word timestamps for the karaoke highlight.
Transcript truth stays with the Speko API (see transcribe.py); correct any
aligner mishears toward the Speko transcript with config "overrides".
"""

import subprocess
import tempfile
from pathlib import Path


def _extract_wav(video: str | Path) -> Path:
    out = Path(tempfile.mkdtemp(prefix="speko-align-")) / (Path(video).stem + ".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
         "-vn", "-ac", "1", "-ar", "16000", str(out)],
        check=True,
    )
    return out


def word_timings(video: str | Path, model: str = "small.en") -> list[dict]:
    """Returns [{"w": word, "s": start, "e": end, "p": probability}, ...]."""
    from faster_whisper import WhisperModel  # lazy: heavy import

    wav = _extract_wav(video)
    wm = WhisperModel(model, device="cpu", compute_type="int8")
    segments, _info = wm.transcribe(str(wav), word_timestamps=True, beam_size=5,
                                    condition_on_previous_text=False)
    words = []
    for seg in segments:
        for w in seg.words:
            words.append({"w": w.word.strip(), "s": round(w.start, 3),
                          "e": round(w.end, 3), "p": round(w.probability, 3)})
    return words


def coverage_gap(words: list[dict], duration: float, tail_margin: float = 2.5) -> float | None:
    """If alignment stopped well before the clip end (crosstalk does this),
    return the time to re-align from; else None."""
    if not words:
        return 0.0
    last = words[-1]["e"]
    if duration - last > tail_margin:
        return max(0.0, last - 1.0)
    return None


def word_timings_tail(video: str | Path, offset: float, model: str = "small.en") -> list[dict]:
    """Re-align only the tail from `offset` seconds (rescues crosstalk cutoffs)."""
    from faster_whisper import WhisperModel  # lazy

    clip = Path(tempfile.mkdtemp(prefix="speko-align-tail-")) / "tail.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{offset:.2f}", "-i", str(video),
         "-vn", "-ac", "1", "-ar", "16000", str(clip)],
        check=True,
    )
    wm = WhisperModel(model, device="cpu", compute_type="int8")
    segments, _info = wm.transcribe(str(clip), word_timestamps=True, beam_size=5,
                                    condition_on_previous_text=False)
    words = []
    for seg in segments:
        for w in seg.words:
            words.append({"w": w.word.strip(), "s": round(w.start + offset, 3),
                          "e": round(w.end + offset, 3), "p": round(w.probability, 3)})
    return words


def merge_tail(words: list[dict], tail: list[dict]) -> list[dict]:
    """Merge a tail re-alignment into the main list without duplicating words."""
    if not words:
        return tail
    cutoff = words[-1]["e"] - 0.05
    fresh = [w for w in tail if w["s"] >= cutoff]
    return words + fresh
