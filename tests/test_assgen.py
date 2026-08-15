"""Deterministic tests: no network, no ffmpeg."""

import itertools
import json
from pathlib import Path

from speko_captions import assgen
from speko_captions.config import load_config

FIX = Path(__file__).parent / "fixtures"


def _words():
    return json.loads((FIX / "words.json").read_text())


def _cfg():
    return load_config(FIX / "config.json")


def test_golden_ass():
    cfg = _cfg()
    words = assgen.apply_overrides(_words(), cfg["overrides"], cfg["filler_strip"])
    got = assgen.build_ass(words, cfg, duration=12.0)
    want = (FIX / "golden.ass").read_text()
    assert got == want


def test_pages_respect_max_words():
    cfg = _cfg()
    words = [{"w": f"w{i}", "s": i * 0.2, "e": i * 0.2 + 0.15, "p": 1.0} for i in range(10)]
    for page in assgen.pages(words, cfg):
        assert len(page) <= cfg["caption"]["max_words"]


def test_pages_break_on_gap():
    cfg = _cfg()
    words = [
        {"w": "a", "s": 0.0, "e": 0.2, "p": 1.0},
        {"w": "b", "s": 0.3, "e": 0.5, "p": 1.0},
        {"w": "c", "s": 2.0, "e": 2.2, "p": 1.0},  # 1.5s gap
    ]
    pgs = assgen.pages(words, cfg)
    assert [len(p) for p in pgs] == [2, 1]


def test_pages_break_after_punctuation():
    cfg = _cfg()
    words = [
        {"w": "done.", "s": 0.0, "e": 0.2, "p": 1.0},
        {"w": "next", "s": 0.25, "e": 0.45, "p": 1.0},
    ]
    pgs = assgen.pages(words, cfg)
    assert [len(p) for p in pgs] == [1, 1]


def test_no_two_pages_visible_at_once():
    """Regression: a page's last event must end by the next page's start."""
    cfg = _cfg()
    words = assgen.apply_overrides(_words(), cfg["overrides"], cfg["filler_strip"])
    ass = assgen.build_ass(words, cfg, duration=12.0)
    cap_events = []
    for line in ass.splitlines():
        if line.startswith("Dialogue: 0,"):
            parts = line.split(",")
            cap_events.append((parts[1], parts[2]))

    def sec(ts):
        h, m, s = ts.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    pgs = assgen.pages(words, cfg)
    idx = 0
    page_spans = []
    for page in pgs:
        first_start = sec(cap_events[idx][0])
        last_end = sec(cap_events[idx + len(page) - 1][1])
        page_spans.append((first_start, last_end))
        idx += len(page)
    for (s1, e1), (s2, e2) in itertools.pairwise(page_spans):
        assert e1 <= s2 + 1e-6, f"page overlap: ends {e1} after next starts {s2}"


def test_filler_strip_merges_time_into_previous_word():
    words = [
        {"w": "useful", "s": 0.6, "e": 0.9, "p": 1.0},
        {"w": "like", "s": 1.0, "e": 1.4, "p": 1.0},
        {"w": "next", "s": 1.5, "e": 1.8, "p": 1.0},
    ]
    out = assgen.apply_overrides(words, [], filler_strip=[1.0])
    assert [w["w"] for w in out] == ["useful", "next"]
    assert out[0]["e"] == 1.4


def test_overrides_substitute_and_merge():
    words = [
        {"w": "plot", "s": 0.0, "e": 0.3, "p": 1.0},
        {"w": "code", "s": 0.35, "e": 0.6, "p": 1.0},
    ]
    out = assgen.apply_overrides(words, [{"from": ["plot", "code"], "to": ["Claude", "Code"]}], [])
    assert [w["w"] for w in out] == ["Claude", "Code"]


def test_hex_to_ass():
    assert assgen.hex_to_ass("#38BDF8") == "&H00F8BD38&"
    assert assgen.hex_to_ass("#FFFFFF") == "&H00FFFFFF&"


def test_case_keep_survives_upper():
    assert assgen.display("ides,", "upper", ["IDEs"]) == "IDEs,"
    assert assgen.display("phone", "upper", []) == "PHONE"


def test_project_transcript_replaces_mishears_keeps_timing():
    words = [
        {"w": "cloud", "s": 0.0, "e": 0.3, "p": 0.2},
        {"w": "code", "s": 0.35, "e": 0.6, "p": 0.3},
        {"w": "ships", "s": 0.65, "e": 0.9, "p": 0.9},
    ]
    out = assgen.project_transcript("Claude Code ships", words)
    assert [w["w"] for w in out] == ["Claude", "Code", "ships"]
    assert out[0]["s"] == 0.0 and out[1]["e"] == 0.6


def test_project_transcript_uneven_replace_spans_window():
    words = [
        {"w": "social", "s": 1.0, "e": 1.3, "p": 0.9},
        {"w": "-ready", "s": 1.32, "e": 1.6, "p": 0.5},
    ]
    out = assgen.project_transcript("social-ready", words)
    assert [w["w"] for w in out] == ["social-ready"]
    assert out[0]["s"] == 1.0 and out[0]["e"] == 1.6


def test_project_transcript_delete_merges_into_previous():
    words = [
        {"w": "hello", "s": 0.0, "e": 0.3, "p": 0.9},
        {"w": "uh", "s": 0.35, "e": 0.5, "p": 0.2},
        {"w": "world", "s": 0.55, "e": 0.9, "p": 0.9},
    ]
    out = assgen.project_transcript("hello world", words)
    assert [w["w"] for w in out] == ["hello", "world"]
    assert out[0]["e"] == 0.5


def test_overrides_expand_without_corrupting_neighbors():
    words = [
        {"w": "we're", "s": 0.0, "e": 0.2, "p": 1.0},
        {"w": "gonna", "s": 0.25, "e": 0.5, "p": 1.0},
        {"w": "ship", "s": 0.55, "e": 0.8, "p": 1.0},
    ]
    out = assgen.apply_overrides(words, [{"from": ["gonna"], "to": ["going", "to"]}], [])
    assert [w["w"] for w in out] == ["we're", "going", "to", "ship"]
    assert out[3] == words[2]


def test_overrides_expand_at_end_of_list():
    words = [{"w": "gonna", "s": 0.0, "e": 0.4, "p": 1.0}]
    out = assgen.apply_overrides(words, [{"from": ["gonna"], "to": ["going", "to"]}], [])
    assert [w["w"] for w in out] == ["going", "to"]


def test_overrides_replace_every_occurrence():
    words = [
        {"w": "cloud", "s": 0.0, "e": 0.2, "p": 1.0},
        {"w": "and", "s": 0.3, "e": 0.4, "p": 1.0},
        {"w": "cloud", "s": 0.5, "e": 0.7, "p": 1.0},
    ]
    out = assgen.apply_overrides(words, [{"from": ["cloud"], "to": ["Claude"]}], [])
    assert [w["w"] for w in out] == ["Claude", "and", "Claude"]
