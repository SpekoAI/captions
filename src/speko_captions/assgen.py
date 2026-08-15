"""Pure ASS-subtitle generation: words + config in, .ass text out.

No I/O, no network, no ffmpeg - fully unit-testable.
"""

import difflib
import re


def hex_to_ass(color: str) -> str:
    """#RRGGBB -> &H00BBGGRR& (ASS is BGR)."""
    c = color.lstrip("#")
    r, g, b = c[0:2], c[2:4], c[4:6]
    return f"&H00{b}{g}{r}&".upper()


def _bare(token: str) -> str:
    return token.strip(".,?!\"'").lower()


def _redistribute(slots: list[dict], tokens: list[str],
                  span: tuple[float, float]) -> list[dict]:
    """Fit `tokens` into the time window `span`, weighting by token length.
    Equal counts keep each slot's own timing."""
    if not tokens:
        return []
    if len(slots) == len(tokens):
        return [{**s, "w": t} for s, t in zip(slots, tokens)]
    s0, e0 = span
    p = min((s.get("p", 1.0) for s in slots), default=0.5)
    weights = [max(1, len(t)) for t in tokens]
    total = sum(weights)
    dur = max(e0 - s0, 0.05 * len(tokens))
    out, cur = [], s0
    for t, wt in zip(tokens, weights):
        d = dur * wt / total
        out.append({"w": t, "s": round(cur, 3), "e": round(cur + d, 3), "p": p})
        cur += d
    out[-1]["e"] = round(max(e0, out[-1]["s"] + 0.05), 3)
    return out


def project_transcript(text: str, words: list[dict]) -> list[dict]:
    """Project the API transcript onto the aligner's word timings.

    The returned words carry the transcript's tokens (text truth) with the
    aligner's timestamps. Aligner-only words merge into their neighbors;
    transcript-only words share the nearest silence or their neighbor's slot.
    """
    if not text.strip() or not words:
        return words
    tokens = text.split()
    a = [_bare(w["w"]) for w in words]
    b = [_bare(t) for t in tokens]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out: list[dict] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.extend({**words[i1 + k], "w": tokens[j1 + k]} for k in range(i2 - i1))
        elif tag == "replace":
            span = (words[i1]["s"], words[i2 - 1]["e"])
            out.extend(_redistribute(words[i1:i2], tokens[j1:j2], span))
        elif tag == "delete":
            if out:
                out[-1]["e"] = words[i2 - 1]["e"]
        elif tag == "insert":
            prev_end = out[-1]["e"] if out else (words[0]["s"] if words else 0.0)
            next_start = words[i1]["s"] if i1 < len(words) else prev_end
            if next_start - prev_end > 0.1 * (j2 - j1):
                out.extend(_redistribute([], tokens[j1:j2], (prev_end, next_start)))
            elif out:
                out[-1] = {**out[-1], "w": out[-1]["w"] + " " + " ".join(tokens[j1:j2])}
            else:
                out.extend(_redistribute([], tokens[j1:j2],
                                         (prev_end, prev_end + 0.3 * (j2 - j1))))
    return out


def apply_overrides(words: list[dict], overrides: list[dict],
                    filler_strip: list[float]) -> list[dict]:
    """Substitute transcript fixes (every occurrence, any length change),
    then hide filler words (their time merges into the previous word)."""
    out = [dict(w) for w in words]

    for rule in overrides:
        src = [s.lower() for s in rule["from"]]
        dst = list(rule["to"])
        n = len(src)
        res: list[dict] = []
        i = 0
        while i < len(out):
            window = [_bare(x["w"]) for x in out[i:i + n]]
            if len(window) == n and window == src:
                span = (out[i]["s"], out[i + n - 1]["e"])
                res.extend(_redistribute(out[i:i + n], dst, span))
                i += n
            else:
                res.append(out[i])
                i += 1
        out = res

    merged: list[dict] = []
    for w in out:
        if any(abs(w["s"] - ft) < 0.05 for ft in filler_strip):
            if merged:
                merged[-1]["e"] = w["e"]
            continue
        merged.append(w)
    return merged


def display(word: str, case: str, case_keep: list[str]) -> str:
    w = re.sub(r"\.+$", "", word)  # drop periods; keep commas and question marks
    bare = w.strip("?,").lower()
    for k in case_keep:
        if bare == k.lower():
            return w.replace(w.strip("?,"), k)
    if case == "upper":
        return w.upper()
    if case == "lower":
        return w.lower()
    return w


def pages(words: list[dict], cfg: dict) -> list[list[dict]]:
    """Phrase-aware paging: cap words and chars per page, break on silence
    gaps and after punctuation."""
    cap = cfg["caption"]
    out: list[list[dict]] = []
    cur: list[dict] = []
    for w in words:
        if cur:
            gap = w["s"] - cur[-1]["e"]
            chars = sum(len(display(x["w"], cap["case"], cfg["case_keep"])) + 1 for x in cur)
            chars += len(display(w["w"], cap["case"], cfg["case_keep"]))
            prev_break = cur[-1]["w"].rstrip()[-1:] in ".?!,"
            if (len(cur) >= cap["max_words"] or chars > cap["max_chars"]
                    or gap > cap["gap_break"] or prev_break):
                out.append(cur)
                cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def _ts(t: float) -> str:
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _header(cfg: dict) -> str:
    cap = cfg["caption"]
    hook = cfg.get("hook") or {}
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {cfg['video']['width']}
PlayResY: {cfg['video']['height']}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{cap['font']},{cap['size']},{hex_to_ass(cap['text_color'])[:-1]},&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,{cap['outline']},{cap['shadow']},5,60,60,0,1
Style: Hook,{cap['font']},{hook.get('size', 64)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,1,0,1,6,2,5,60,60,0,1
Style: Tag,Geist SemiBold,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&HFF000000,0,0,0,0,100,100,0.5,0,1,4,1,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def build_ass(words: list[dict], cfg: dict, duration: float) -> str:
    cap = cfg["caption"]
    cx = cfg["video"]["width"] // 2
    active = hex_to_ass(cap["active_color"])
    text_c = hex_to_ass(cap["text_color"])
    pop = round(cap["pop"] * 100)
    pre = min(104, pop)

    ev: list[str] = []
    hook = cfg.get("hook")
    if hook and hook.get("text"):
        ev.append(
            f"Dialogue: 1,{_ts(0)},{_ts(hook.get('seconds', 2.2))},Hook,,0,0,0,,"
            f"{{\\pos({cx},{hook.get('y', 300)})\\fad(120,150)}}{hook['text']}"
        )
    for tag in cfg.get("tags", []):
        text = tag["text"]
        if tag.get("subtext"):
            text += f" \\N{{\\fs32}}{tag['subtext']}"
        ev.append(
            f"Dialogue: 1,{_ts(tag['start'])},{_ts(tag['start'] + tag.get('dur', 3.0))},Tag,,0,0,0,,"
            f"{{\\pos({cx},{cap['y'] - 130})\\fad(150,150)}}{text}"
        )

    pgs = pages(words, cfg)
    for pi, page in enumerate(pgs):
        page_end = min(page[-1]["e"] + 0.12, duration)
        if pi + 1 < len(pgs):
            page_end = min(page_end, pgs[pi + 1][0]["s"])
        for i, w in enumerate(page):
            start = w["s"]
            end = page[i + 1]["s"] if i + 1 < len(page) else page_end
            if end <= start:
                end = start + 0.05
            parts = []
            for j, x in enumerate(page):
                d = display(x["w"], cap["case"], cfg["case_keep"])
                if j == len(page) - 1:
                    d = d.rstrip(",")
                if j == i and cap["pop"] > 1.0:
                    parts.append(
                        f"{{\\c{active}\\fscx{pre}\\fscy{pre}"
                        f"\\t(0,70,\\fscx{pop}\\fscy{pop})}}{d}{{\\r}}"
                    )
                elif j == i:
                    parts.append(f"{{\\c{active}}}{d}{{\\r}}")
                else:
                    parts.append(f"{{\\c{text_c}}}{d}{{\\r}}")
            ev.append(
                f"Dialogue: 0,{_ts(start)},{_ts(end)},Cap,,0,0,0,,"
                f"{{\\pos({cx},{cap['y']})}}{' '.join(parts)}"
            )
    return _header(cfg) + "\n".join(ev) + "\n"
