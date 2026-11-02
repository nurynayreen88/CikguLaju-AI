"""Read verified Year 4 standalone lesson text into RPH rows; never modify source or DB."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent / "rph_standalone" / "english" / "year4"
HEADING = re.compile(r"(?m)^##\s+([^\n]+)\n")
META = re.compile(r"(?m)^\*\*(?:QA|Status|Resource status|SOW reference|Source):\*\*")


def apply(st, rows):
    if not isinstance(st, dict) or not isinstance(rows, dict):
        return rows
    if str(st.get("subject", "")).strip().casefold() not in ("english", "bahasa inggeris"):
        return rows
    if str(st.get("year", "")).strip().casefold() not in ("tahun 4", "year 4", "4"):
        return rows
    try:
        lesson = int(st.get("lesson_no") or st.get("textbook_lesson_no") or st.get("lesson"))
    except (ValueError, TypeError):
        return rows
    if not 1 <= lesson <= 160:
        return rows
    path = ROOT / ("lesson_%03d.md" % lesson)
    if not path.is_file():
        return rows
    source = path.read_text(encoding="utf-8")
    matches = list(HEADING.finditer(source))
    phases = []
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        body = source[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(source)]
        body = META.split(body, maxsplit=1)[0].strip()
        phases.append((title, body))

    def first(prefixes):
        return next((body for title, body in phases if title.casefold().startswith(prefixes) and body), "")

    intro = first(("set induction",))
    closure = first(("closure",))
    activities = [(title, body) for title, body in phases if re.match(r"(?i)^activity\s+[1-9]", title) and body]
    pbd = first(("reinforcement / pbd", "pbd / reinforcement", "assessment", "pbd /", "pbd and differentiation"))
    if not intro or not closure or not activities:
        return rows

    def clean(value):
        value = re.sub(r"\*\*(Teacher|Pupils|Teacher action|Pupil action):\*\*", r"\n\1:", value)
        value = re.sub(r"\*\*([^*\n]+)\*\*", r"\1", value)
        return value.strip()

    result = dict(rows)
    result["SET INDUKSI"] = clean(intro)
    parts = [title + "\n" + clean(body) for title, body in activities]
    if pbd:
        parts.append("Assessment / PBD\n" + clean(pbd))
        result["PENTAKSIRAN"] = clean(pbd)
    result["AKTIVITI UTAMA"] = "\n\n".join(parts)
    result["PENUTUP"] = clean(closure)
    ref = re.search(r"(?mi)^\*\*(?:Materials|References|Resources):\*\*\s*(.*)$", source)
    if ref:
        result["BAHAN BANTU MENGAJAR"] = ref.group(1).strip()
    result["_standalone_y4_source"] = str(path.relative_to(ROOT.parent.parent.parent))
    return result
