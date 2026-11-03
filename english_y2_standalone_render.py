"""English Year 2 standalone lesson content -> existing RPH row renderer.
No database writes; missing lessons fall back to the existing generator.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent / "rph_standalone" / "english" / "year2"

def _section(source, name):
    match = re.search(r"(?m)^## " + re.escape(name) + r"\s*\([^\n]*\)\s*\n(.*?)(?=^## |^\*\*(?:QA(?: status)?|Status|Source|Official SOW alignment|Release gate|Verification):\*\*|\Z)", source, re.S | re.M)
    return match.group(1).strip() if match else ""

def apply(st, rows):
    if not isinstance(st, dict) or not isinstance(rows, dict):
        return rows
    if str(st.get("subject", "")).strip().casefold() not in ("english", "bahasa inggeris"):
        return rows
    if str(st.get("year", "")).strip().casefold() not in ("tahun 2", "year 2", "2"):
        return rows
    # Reject coercible invalid IDs (True, 1.5) and stale callback identifiers.
    raw = st.get("lesson_no")
    if raw is None or raw == "":
        raw = st.get("textbook_lesson_no")
    if raw is None or raw == "":
        raw = st.get("lesson")
    if type(raw) is int:
        lesson = raw
    elif isinstance(raw, str) and raw.strip().isascii() and raw.strip().isdecimal():
        lesson = int(raw.strip())
    else:
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
        match = re.search(r"(?m)^## (" + re.escape(prefix) + r"[^\n]*)\n(.*?)(?=^## |^\*\*(?:QA(?: status)?|Status|Source|Official SOW alignment|Release gate|Verification):\*\*|\Z)", source, re.S | re.M)
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
        result["PENTAKSIRAN"] = assessment
    result["AKTIVITI UTAMA"] = "\n\n".join(lines)
    # Internal QA notes belong in source audits, never in teacher-facing RPH.
    closure = re.split(r"(?im)^\s*\*\*(?:QA(?: status)?|Status|Source|Official SOW alignment|Release gate|Verification):\*\*", closure, maxsplit=1)[0].strip()
    result["PENUTUP"] = closure
    ref = re.search(
        r"(?im)^\*\*(?:References|Teaching materials|Materials(?:\s*/\s*references)?|Resources):\*\*\s*([^\n]+)",
        source)
    if ref:
        result["BAHAN BANTU MENGAJAR"] = ref.group(1).strip()
    result["_standalone_y2_source"] = str(path.relative_to(ROOT.parent.parent.parent))
    return result
