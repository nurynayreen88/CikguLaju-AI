"""English Year 3 standalone lesson content -> existing RPH row renderer.
No database writes; missing lessons fall back to the existing generator.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent / "rph_standalone" / "english" / "year3"

def _section(source, name):
    match = re.search(r"(?m)^## " + re.escape(name) + r"\s*\([^\n]*\)\s*\n(.*?)(?=^## |^\*\*QA:|\Z)", source, re.S | re.M)
    return match.group(1).strip() if match else ""

def apply(st, rows):
    if not isinstance(st, dict) or not isinstance(rows, dict):
        return rows
    if str(st.get("subject", "")).strip().casefold() not in ("english", "bahasa inggeris"):
        return rows
    if str(st.get("year", "")).strip().casefold() not in ("tahun 3", "year 3", "3"):
        return rows
    try:
        lesson = int(st.get("lesson_no") or st.get("textbook_lesson_no") or st.get("lesson"))
    except (TypeError, ValueError):
        return rows
    if not 1 <= lesson <= 160:
        return rows
    path = ROOT / ("lesson_%03d.md" % lesson)
    if not path.is_file():
        return rows
    source = path.read_text(encoding="utf-8")
    # Match teaching phases regardless of heading capitalization or duration.
    def get(prefix):
        match = re.search(r"^##\s+(" + re.escape(prefix) + r"[^\n]*)\n(.*?)(?=^##\s+|^\*\*(?:QA(?: status)?|Status|Resource status|Source):|\Z)", source, re.S | re.M | re.I)
        return (match.group(1).strip(), match.group(2).strip()) if match else ("", "")
    intro = get("Set Induction")[1]
    activities = [get("Activity " + str(i)) for i in range(1, 5)]
    assessment = get("Assessment")[1] or get("Reinforcement / PBD")[1] or get("PBD / reinforcement")[1] or get("PBD")[1]
    closure = get("Closure")[1]
    if not intro or not any(body for _, body in activities) or not closure or not assessment:
        return rows
    if re.search(r"(?mi)^\*\*(?:QA(?: status)?|Status|Resource status):\*\*[^\n]*(?:DRAFT|NOT READY|not READY|do not publish|pending)", source):
        return rows
    result = dict(rows)
    def clean_phase(text):
        # Preserve actions while making teacher and pupil roles separate lines.
        text = re.sub(r"\*\*(Teacher|Pupils):\*\*", r"\n\1:", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"(?m)^[ \t]*\n", "", text)
        return text.strip()
    result["SET INDUKSI"] = clean_phase(intro)
    lines = [title + "\n" + clean_phase(body) for title, body in activities if body]
    if assessment:
        lines.append("Assessment / PBD\n" + clean_phase(assessment))
        result["PENTAKSIRAN"] = clean_phase(assessment)
    result["AKTIVITI UTAMA"] = "\n\n".join(lines)
    # Closure is the last teaching phase; omit subsequent resource/QA metadata.
    closure = re.split(r"(?mi)^\s*(?:\*\*(?:QA(?: status)?|Status|Resource status|Source|PBD|Differentiation):|## )", closure, maxsplit=1)[0]
    result["PENUTUP"] = clean_phase(closure)
    ref = re.search(r"(?m)^\*\*(?:References|Materials):\*\*\s*(.*)$", source)
    if ref:
        result["BAHAN BANTU MENGAJAR"] = ref.group(1).strip()
    result["_standalone_y3_source"] = str(path.relative_to(ROOT.parent.parent.parent))
    return result
