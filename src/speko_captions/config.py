"""Per-video config: one JSON file controls everything an editor would touch."""

import copy
import json
from pathlib import Path

DEFAULTS = {
    # Burned caption block.
    "caption": {
        "font": "Geist Black",
        "size": 88,
        "y": 1150,             # block center on the 1080x1920 canvas; clears TikTok
        #                        bottom UI and the YouTube Shorts worst case (y>1248)
        "text_color": "#FFFFFF",
        "active_color": "#38BDF8",
        "outline": 7,
        "shadow": 2,
        "max_words": 4,        # words per page
        "max_chars": 18,       # display chars per page
        "gap_break": 0.55,     # silence gap (s) that forces a new page
        "case": "upper",       # upper | keep | lower
        "pop": 1.08,           # active-word scale factor (1.0 disables)
    },
    # Optional top hook text shown at the start.
    "hook": None,              # {"text": "LINE ONE\\NLINE TWO", "seconds": 2.2,
    #                            "y": 300, "size": 64}
    # Optional name tags (speaker lower-thirds).
    "tags": [],                # [{"text": "NAME", "subtext": "TITLE",
    #                             "start": 17.3, "dur": 3.0}]
    # Start times (s) of filler words to hide from captions (audio unchanged;
    # timing merges into the previous word). Find them in words.json.
    "filler_strip": [],
    # Word substitutions toward the Speko transcript (timing kept):
    # [{"from": ["plot", "code"], "to": ["Claude", "Code"]}]
    "overrides": [],
    # Words whose casing must survive the case transform, e.g. ["IDEs", "iMessage"].
    "case_keep": [],
    "audio": {
        "target_i": -14.0,     # integrated LUFS for social feeds
        "target_tp": -1.5,
        "target_lra": 11.0,
        "highpass": 80,
        "denoise": True,
        "presence_eq": True,   # +2dB at 2.5kHz for speech clarity
        "fade_out": 0.25,
    },
    "video": {
        "width": 1080,
        "height": 1920,
        "crf": 18,
        "fade_out": 0.29,
        "sharpen": True,
    },
    "stt": {
        "language": "en",
        "pin": None,           # e.g. "alibaba:qwen3-asr-flash"; None lets the
        #                        Speko router pick the lane
    },
    "align": {
        "model": "small.en",   # faster-whisper model for word timings
    },
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_config(path: str | Path | None) -> dict:
    if path is None:
        return copy.deepcopy(DEFAULTS)
    data = json.loads(Path(path).read_text())
    return _merge(DEFAULTS, data)
