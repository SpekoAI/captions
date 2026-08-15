"""Pure ASS-subtitle generation: words + config in, .ass text out.

No I/O, no network, no ffmpeg - fully unit-testable.
"""

import re


def hex_to_ass(color: str) -> str:
    """#RRGGBB -> &H00BBGGRR& (ASS is BGR)."""
    c = color.lstrip("#")
    r, g, b = c[0:2], c[2:4], c[4:6]
    return f"&H00{b}{g}{r}&".upper()


def apply_overrides(words: list[dict], overrides: list[dict],
                    filler_strip: list[float]) -> list[dict]:
    """Substitute aligner mishears toward the Speko transcript, then hide
    filler words (their time merges into the previous word)."""
    txt = [w["w"] for w in words]

    for rule in overrides:
        src = [s.lower() for s in rule["from"]]
        dst = list(rule["to"])
        n = len(src)
        for i in range(len(txt) - n + 1):
            window = [t.lower().strip(".,?!") for t in txt[i:i + n]]
            if window == src:
                for j, t in enumerate(dst):
                    txt[i + j] = t
                for j in range(len(dst), n):
                    words[i + len(dst) - 1]["e"] = words[i + j]["e"]
                    txt[i + j] = ""
                break

    merged: list[dict] = []
    for w, t in zip(words, txt):
        if not t:
            continue
        if any(abs(w["s"] - ft) < 0.05 for ft in filler_strip):
            if merged:
                merged[-1]["e"] = w["e"]
            continue
        merged.append({**w, "w": t})
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
