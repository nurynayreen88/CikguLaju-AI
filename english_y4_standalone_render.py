"""Opt-in, read-only English Year 4 standalone preview for RPH rows.

This module deliberately does NOT approve a lesson, send Telegram messages,
write a database or override the existing renderer by default. Only vetted
fixed-SOW provisional sources may be previewed in isolated staging.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent / "rph_standalone" / "english" / "year4"
HEADING = re.compile(r"(?m)^##[ \t]+([^\n]+)\n")
QA = re.compile(r"(?mi)^\*\*QA status:\*\*\s*([^\n]+)")
METADATA = re.compile(
    r"(?mi)^\*\*(?:QA(?: status)?|Status|Resource status|SOW reference|Source):\*\*"
)
NUMERIC_LS = re.compile(r"\b\d\.\d\.\d\b")
UNSAFE_AUDIO = re.compile(
    r"audio pending verification|audio delivery.*pending|"
    r"do not play or send|neither CD1 nor CD2|"
    r"listening SP\s*1\.2\.5\s+is pending",
    re.I,
)


def _valid_lesson(state):
    for name in ("lesson_no", "textbook_lesson_no", "lesson"):
        raw = state.get(name)
        if raw is not None and raw != "":
            break
    else:
        return None
    if type(raw) is int:
        value = raw
    elif isinstance(raw, str) and raw.strip().isascii() and raw.strip().isdecimal():
        value = int(raw.strip())
    else:
        return None
    return value if 1 <= value <= 160 else None


def _clean(text):
    text = re.sub(
        r"\*\*(Teacher action|Pupil action|Teacher|Pupils):\*\*",
        lambda m: "\n" + m.group(1) + ":",
        text,
        flags=re.I,
    )
    text = re.sub(r"\*\*([^*\n]+)\*\*", r"\1", text)
    return text.strip()


def apply(state, rows, *, allow_provisional=False):
    """Return new RPH rows only for explicitly opted-in safe previews.

    Provisional is NOT teacher approval. Every other case, including a
    disabled feature, ambiguous lesson, unapproved audio or teacher-choice
    lesson, returns the original rows object unchanged.
    """
    if not allow_provisional or not isinstance(state, dict) or not isinstance(rows, dict):
        return rows
    if str(state.get("subject", "")).strip().casefold() not in ("english", "bahasa inggeris"):
        return rows
    if str(state.get("year", "")).strip().casefold() not in ("year 4", "tahun 4", "4"):
        return rows
    lesson = _valid_lesson(state)
    if lesson is None or lesson == 30:
        return rows

    path = ROOT / ("lesson_%03d.md" % lesson)
    if not path.is_file():
        return rows
    source = path.read_text(encoding="utf-8")
    status = QA.search(source)
    if not status:
        return rows
    label = status.group(1).strip().casefold()
    if not (re.match(r"ready\s*[—–-]\s*provisional\b", label)
            and "pending teacher's final review" in label):
        return rows
    if re.search(r"(?mi)^\*\*(?:Main|Complementary)\s+(?:SK/SP|SP|CS/LS):\*\*\s*(?:Teacher.selected|PILIHAN GURU)", source):
        return rows
    # Keep audio-dependent Year 4 lessons on the existing verified route.
    # Track numbers/filenames alone do not prove spoken content or delivery.
    if UNSAFE_AUDIO.search(source) or re.search(
        r"(?i)\b(?:CD[123]|Track\s*\d+|listen(?:ing)?|audio recording)\b", source
    ) or re.search(r"(?i)\bNOT READY FOR RELEASE\b", source):
        return rows

    # Require an actual numeric official Learning Standard for BOTH skills.
    header = source.split("\n## ", 1)[0]
    main = re.search(r"(?mi)^\*\*Main (?:SK/SP|SP):\*\*([^\n]+)", header)
    comp = re.search(r"(?mi)^\*\*Complementary (?:SK/SP|SP):\*\*([^\n]+)", header)
    if not (main and comp and NUMERIC_LS.search(main.group(1)) and NUMERIC_LS.search(comp.group(1))):
        return rows

    matches = list(HEADING.finditer(source))
    phases = []
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        body = source[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(source)]
        body = METADATA.split(body, maxsplit=1)[0].strip()
        phases.append((title, body))

    def pick(prefixes):
        return next(((title, body) for title, body in phases
                     if title.casefold().startswith(prefixes) and body), None)

    intro = pick(("set induction",))
    close = pick(("closure",))
    pbd = pick(("reinforcement", "pbd /", "pbd and", "assessment"))
    activities = [(title, body) for title, body in phases
                  if re.match(r"(?i)^activity\s+[1-9](?![0-9])", title) and body]
    if not (intro and close and pbd and activities):
        return rows
    # Ignore non-teaching headings but enforce exactly 60 scheduled minutes.
    timed = [intro, *activities, pbd, close]
    mins = []
    for title, body in timed:
        m = re.search(r"\((\d+)\s+minutes?\)", title, re.I)
        if not m or not re.search(r"\*\*(?:Teacher|Teacher action):\*\*", body, re.I) or not re.search(
            r"\*\*(?:Pupils|Pupil action):\*\*", body, re.I
        ):
            return rows
        mins.append(int(m.group(1)))
    if sum(mins) != 60:
        return rows

    result = dict(rows)
    result["SET INDUKSI"] = _clean(intro[1])
    result["AKTIVITI UTAMA"] = "\n\n".join(title + "\n" + _clean(body) for title, body in activities)
    result["PENTAKSIRAN"] = _clean(pbd[1])
    result["PENUTUP"] = _clean(close[1])
    refs = re.search(r"(?mi)^\*\*(?:References|Materials|Resources):\*\*\s*([^\n]+)", header)
    if refs:
        result["BAHAN BANTU MENGAJAR"] = refs.group(1).strip()
    result["_standalone_y4_source"] = str(path.relative_to(ROOT.parent.parent.parent))
    result["_standalone_y4_preview_only"] = True
    return result
