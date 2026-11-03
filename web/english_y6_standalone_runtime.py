"""Isolated English Year 6 RPH 2027 renderer bridge.

Read existing 160 standalone source files. Never touch DB, quotas, Telegram callbacks
or other subjects/years. The existing RPH generator and its quota gate remain in charge.
"""
from pathlib import Path
import re
import json

LESSON_ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english" / "year6"
ALLOWED = frozenset(range(1, 161))
PHASES = ("Set induction", "Activity 1", "Activity 2", "Activity 3", "Reinforcement / PBD", "Closure")


def _target(state):
    if not isinstance(state, dict):
        return None
    subject = re.sub(r"[^a-z]", "", str(state.get("subject") or "").casefold())
    if subject not in ("english", "bahasainggeris", "bi"):
        return None
    year = str(state.get("year") or state.get("year_label") or "").strip().casefold()
    if year not in ("6", "tahun 6", "year 6", "primary year 6", "y6", "tahun 6 (sk)"):
        return None
    raw = state.get("lesson_no") or state.get("textbook_lesson_no") or state.get("lesson")
    if isinstance(raw, bool):
        return None
    raw = str(raw or "").strip()
    if not raw.isascii() or not raw.isdecimal():
        return None
    number = int(raw)
    return number if number in ALLOWED else None


def _clean(raw):
    return re.sub(r"\*\*(.*?)\*\*", r"\1", raw).strip()


def load_lesson(number, *, root=LESSON_ROOT):
    if type(number) is not int or number not in ALLOWED:
        return None
    path = Path(root) / ("lesson_%03d.md" % number)
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if not re.search(r"(?m)^# English Year 6 — Lesson %03d:" % number, content):
        return None
    meta = {}
    for m in re.finditer(r"(?m)^\*\*([^\n*]+):\*\*\s*([^\n]+)", content):
        meta[m.group(1).strip().casefold()] = m.group(2).strip()
    sections = {}
    for m in re.finditer(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", content):
        title = m.group(1).strip()
        sections[title.split(" (")[0].split(" — ")[0]] = _clean(m.group(2))
    if not all(sections.get(p) for p in PHASES):
        return None
    if not all(meta.get(p) for p in ("main cs/ls", "complementary cs/ls",
                                    "learning objective", "pbd evidence", "materials")):
        return None
    return meta, sections


def _overlay(number, root):
    # The official-SOW-derived mapping is version-locked and read-only.
    path = Path(root) / "sow_task_overlay_2027.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version") != "y6-sow-20261103" or data.get("fixed_standard_lessons") != 146:
            return None
        lesson = data["lessons"].get(str(number))
        return lesson if isinstance(lesson, dict) else None
    except (OSError, ValueError, TypeError, KeyError):
        return None


def _phase(text, minutes):
    return "%s minutes\n%s" % (minutes, text)


def _standard_pair(raw):
    result = re.fullmatch(r"([1-5]\.\d)/([1-5]\.\d\.\d)", raw.strip())
    if not result:
        return None
    if not result.group(2).startswith(result.group(1) + "."):
        return None
    return result.groups()


def _source_matches_selected_standard(state, source):
    pair = _standard_pair(source)
    if pair is None:
        return "PILIHAN GURU" in source
    selected = str(state.get("sp_code") or state.get("learning_standard") or "").strip()
    # A separately verified SOW row can veto a conflicting lesson selection.
    if selected and selected != pair[1] and selected != source:
        return False
    return True


def adapt_rows(state, rows, *, root=LESSON_ROOT):
    number = _target(state)
    if number is None or not isinstance(rows, dict):
        return rows
    record = load_lesson(number, root=root)
    if record is None:
        return rows
    meta, p = record
    if not _source_matches_selected_standard(state, meta["main cs/ls"]):
        return rows
    main = _standard_pair(meta["main cs/ls"])
    comp = _standard_pair(meta["complementary cs/ls"])
    overlay = _overlay(number, root)
    # Fixed-standard lessons require matching official SOW codes and a complete
    # task overlay; do not show an uncorrected generic plan on mismatch.
    if main is not None:
        if (not overlay or not comp or overlay.get("main_ls") != main[1]
                or overlay.get("complementary_ls") != comp[1]
                or len(overlay.get("activities") or []) != 3):
            return rows
    result = dict(rows)
    if main and comp:
        result["STANDARD KANDUNGAN"] = "Main: %s; Complementary: %s" % (main[0], comp[0])
        result["STANDARD PEMBELAJARAN"] = "Main: %s; Complementary: %s" % (main[1], comp[1])
    else:
        result["STANDARD KANDUNGAN"] = "Teacher-selected DSKP standard (not fixed by SOW)"
        result["STANDARD PEMBELAJARAN"] = "Teacher-selected DSKP Learning Standard (not fixed by SOW)"
    result["TAJUK"] = meta.get("topic") or rows.get("TAJUK", "")
    result["OBJEKTIF PEMBELAJARAN"] = overlay.get("objective") if overlay else meta["learning objective"]
    result["KRITERIA KEJAYAAN"] = result["OBJEKTIF PEMBELAJARAN"]
    result["BAHAN BANTU MENGAJAR"] = meta["materials"]
    if overlay and overlay.get("sow_pupil_book_exercises"):
        result["BAHAN BANTU MENGAJAR"] += "; SOW PB Exercise(s): " + overlay["sow_pupil_book_exercises"]
    result["PENTAKSIRAN"] = overlay.get("pbd_evidence") if overlay else meta["pbd evidence"]
    if overlay:
        intro = overlay["induction"]
        result["SET INDUKSI"] = _phase("Teacher: " + intro["teacher"] + "\nPupils: " + intro["pupils"], 5)
        detail = []
        for index, minutes in enumerate((10, 18, 15)):
            activity = overlay["activities"][index]
            detail.append("Activity %d (%d minutes)\nTeacher: %s\nPupils: %s" % (
                index + 1, minutes, activity["teacher"], activity["pupils"]))
        detail.append("Reinforcement / PBD (8 minutes)\n" + p["Reinforcement / PBD"])
        result["AKTIVITI UTAMA"] = "\n\n".join(detail)
        ending = overlay["closure"]
        result["PENUTUP"] = _phase("Teacher: " + ending["teacher"] + "\nPupils: " + ending["pupils"], 4)
    else:
        result["SET INDUKSI"] = _phase(p["Set induction"], 5)
        result["AKTIVITI UTAMA"] = "\n\n".join([
            "Activity 1 (10 minutes)\n" + p["Activity 1"],
            "Activity 2 (18 minutes)\n" + p["Activity 2"],
            "Activity 3 (15 minutes)\n" + p["Activity 3"],
            "Reinforcement / PBD (8 minutes)\n" + p["Reinforcement / PBD"],
        ])
        result["PENUTUP"] = _phase(p["Closure"], 4)
    result["PEMULIHAN / PENGAYAAN"] = p.get("Differentiation and follow-up") or rows.get("PEMULIHAN / PENGAYAAN", "")
    result["REFLEKSI"] = meta.get("teacher reflection", rows.get("REFLEKSI", ""))
    return result


def install(runtime):
    """Wrap only the final RPH row constructor; leave all other behaviour intact."""
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y6_RPH_2027_ACTIVE", False):
        return True
    previous = getattr(runtime, "_rph_rows", None)
    if not callable(previous):
        return False

    def year6_rows(state, *args, **kwargs):
        rows = previous(state, *args, **kwargs)
        try:
            return adapt_rows(state, rows)
        except Exception as exc:
            print("ENGLISH Y6 RPH source fallback:", repr(exc), flush=True)
            return rows

    runtime._rph_rows = year6_rows
    runtime.CIKGULAJU_ENGLISH_Y6_RPH_2027_ACTIVE = True
    return True
