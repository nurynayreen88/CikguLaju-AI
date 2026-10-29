"""English Year 2 standalone lesson content -> existing RPH row renderer.
No database writes; missing lessons fall back to the existing generator.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent / "rph_standalone" / "english" / "year2"

def _section(source, name):
    match = re.search(r"(?m)^## " + re.escape(name) + r"\s*\([^\n]*\)\s*\n(.*?)(?=^## |^\*\*QA:|\Z)", source, re.S | re.M)
    return match.group(1).strip() if match else ""

def apply(st, rows):
    if not isinstance(st, dict) or not isinstance(rows, dict):
        return rows
    if str(st.get("subject", "")).strip().casefold() not in ("english", "bahasa inggeris"):
        return rows
    if str(st.get("year", "")).strip().casefold() not in ("tahun 2", "year 2", "2"):
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
    sections = [
        ("Set Induction", "SET INDUKSI"),
        ("Activity 1", None),
        ("Activity 2", None),
        ("Assessment / PBD", "PENTAKSIRAN"),
        ("Closure", "PENUTUP"),
    ]
    # The lesson files may vary in activity titles. Match by phase prefix.
    def get(prefix):
        match = re.search(r"(?m)^## (" + re.escape(prefix) + r"[^\n]*)\n(.*?)(?=^## |^\*\*QA:|\Z)", source, re.S | re.M)
        return (match.group(1).strip(), match.group(2).strip()) if match else ("", "")
    intro = get("Set Induction")[1]
    activities = [get("Activity " + str(i)) for i in range(1, 5)]
    assessment = get("Assessment")[1]
    closure = get("Closure")[1]
    if not intro or not any(body for _, body in activities) or not closure:
        return rows
    result = dict(rows)
    result["SET INDUKSI"] = intro
    lines = [title + "\n" + body for title, body in activities if body]
    if assessment:
        lines.append("Assessment / PBD\n" + assessment)
        result["PENTAKSIRAN"] = assessment
    result["AKTIVITI UTAMA"] = "\n\n".join(lines)
    result["PENUTUP"] = closure
    ref = re.search(r"(?m)^\*\*References:\*\*\s*(.*)$", source)
    if ref:
        result["BAHAN BANTU MENGAJAR"] = ref.group(1).strip()
    result["_standalone_y2_source"] = str(path.relative_to(ROOT.parent.parent.parent))
    return result
