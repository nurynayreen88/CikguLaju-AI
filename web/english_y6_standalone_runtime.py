"""Isolated English Year 6 RPH 2027 renderer bridge.

Read existing 160 standalone source files. Never touch DB, quotas, Telegram callbacks
or other subjects/years. The existing RPH generator and its quota gate remain in charge.
"""
from pathlib import Path
import re
import json

LESSON_ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english" / "year6"
ALLOWED = frozenset(range(1, 161))

OFFICIAL_SOW_INDEX = Path(__file__).resolve().parents[1] / "audits" / "english_primary_2_6_official_sow_index_20261103.json"
OFFICIAL_SOW_VERSION = "2026-11-03-source-table-2-6"
Y6_TEACHER_CHOICES = frozenset((16, 32, 48, 64, 80, 96, 112, 128, 144, 155, 156, 157, 158, 160))
TEACHER_SELECTED_STANDARD = "Teacher to choose Year 6 DSKP standard (not fixed by SOW)"


def _official_y6_sow(number, *, index_path=OFFICIAL_SOW_INDEX):
    """Require exact Year6 lesson identity and a complete 160-row source index."""
    if type(number) is not int or not 1 <= number <= 160:
        return None
    try:
        data = json.loads(Path(index_path).read_text(encoding="utf-8"))
        lessons = data.get("lessons")
        if data.get("version") != OFFICIAL_SOW_VERSION or not isinstance(lessons, dict):
            return None
        if sum(k.startswith("6/") for k in lessons) != 160:
            return None
        rec = lessons.get("6/%d" % number)
        return rec if isinstance(rec, dict) and rec.get("n") == number else None
    except (OSError, ValueError, TypeError):
        return None


def _teacher_choice_sow(number, *, index_path=OFFICIAL_SOW_INDEX):
    """Reject stale/unverified teacher-choice mappings; never invent CS/LS."""
    if type(number) is not int or number not in Y6_TEACHER_CHOICES:
        return None
    try:
        data = json.loads(Path(index_path).read_text(encoding="utf-8"))
        lessons = data.get("lessons")
        if data.get("version") != OFFICIAL_SOW_VERSION or not isinstance(lessons, dict):
            return None
        if sum(k.startswith("6/") for k in lessons) != 160:
            return None
        rec = lessons.get("6/%d" % number)
        if (not isinstance(rec, dict) or rec.get("n") != number
                or rec.get("teacher_selected") is not True
                or rec.get("main_ls") is not None
                or rec.get("complementary_ls") is not None):
            return None
        return rec
    except (OSError, ValueError, TypeError):
        return None


def _teacher_choice_title(record):
    """Use SOW topic where fixed; otherwise make suggested status explicit."""
    topic = str(record.get("topic") or "").strip()
    focus = str(record.get("focus") or "").strip()
    if not topic or topic.lower().startswith(("teacher to select", "teacher to complete")):
        return "CADANGAN CIKGULAJU (DRAF) — %s — topic selected by teacher" % focus
    return "CADANGAN CIKGULAJU (DRAF) — %s — %s" % (topic, focus)

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
    sow_entry = _official_y6_sow(number)
    if sow_entry is None:
        return rows
    # Fixed-standard lessons require matching official SOW codes and a complete
    # task overlay; do not show an uncorrected generic plan on mismatch.
    if main is not None:
        if (not overlay or not comp or sow_entry.get("teacher_selected") is not False
                or sow_entry.get("main_ls") != main[1]
                or sow_entry.get("complementary_ls") != comp[1]
                or overlay.get("main_ls") != main[1]
                or overlay.get("complementary_ls") != comp[1]
                or len(overlay.get("activities") or []) != 3):
            return rows
    # Teacher-choice Lesson must be confirmed independently against the
    # complete official SOW index; the source markdown alone is insufficient.
    choice_sow = None
    if main is None:
        if comp is not None or ("PILIHAN GURU" not in meta["main cs/ls"]
                                or "PILIHAN GURU" not in meta["complementary cs/ls"]):
            return rows
        choice_sow = _teacher_choice_sow(number)
        if choice_sow is None:
            return rows
    # Native English Word/PDF tables read four separate standard fields.
    # Never let the legacy document's numeric codes leak into 14 lessons for
    # which the official SOW specifies that the teacher selects the standards.
    if main and comp:
        for key, expected in (("comp_sp_code", comp[1]),
                              ("bi_comp_sp_code", comp[1]),
                              ("bi_main_sp_code", main[1])):
            selected = str(state.get(key) or "").strip()
            if selected and selected != expected:
                return rows
    result = dict(rows)
    if main and comp:
        result["MAIN CONTENT STANDARD"] = main[0]
        result["MAIN LEARNING STANDARD"] = main[1]
        result["COMPLEMENTARY CONTENT STANDARD"] = comp[0]
        result["COMPLEMENTARY LEARNING STANDARD"] = comp[1]
        result["STANDARD KANDUNGAN"] = "Main: %s; Complementary: %s" % (main[0], comp[0])
        result["STANDARD PEMBELAJARAN"] = "Main: %s; Complementary: %s" % (main[1], comp[1])
    else:
        for field in ("MAIN CONTENT STANDARD", "MAIN LEARNING STANDARD",
                      "COMPLEMENTARY CONTENT STANDARD", "COMPLEMENTARY LEARNING STANDARD",
                      "STANDARD KANDUNGAN", "STANDARD PEMBELAJARAN"):
            result[field] = TEACHER_SELECTED_STANDARD
    if choice_sow is not None:
        result["TAJUK"] = _teacher_choice_title(choice_sow)
    else:
        # Year6 source Markdown often has no **Topic:** header. Use the
        # official SOW topic/focus, not a legacy generic title from the old
        # application RPH. This is not evidence of final teacher approval.
        official_topic = str(sow_entry.get("topic") or "").strip()
        official_focus = str(sow_entry.get("focus") or "").strip()
        if not official_topic or official_topic.lower().startswith("teacher to"):
            return rows
        result["TAJUK"] = official_topic + (" — " + official_focus if official_focus else "")
    result["OBJEKTIF PEMBELAJARAN"] = overlay.get("objective") if overlay else meta["learning objective"]
    result["KRITERIA KEJAYAAN"] = result["OBJEKTIF PEMBELAJARAN"]
    result["BAHAN BANTU MENGAJAR"] = meta["materials"]
    if overlay and overlay.get("sow_pupil_book_exercises"):
        result["BAHAN BANTU MENGAJAR"] += "; SOW PB Exercise(s): " + overlay["sow_pupil_book_exercises"]
    result["PENTAKSIRAN"] = overlay.get("pbd_evidence") if overlay else meta["pbd evidence"]
    if choice_sow is not None:
        # For teacher-selected Lessons the short PBD evidence label alone
        # omits the teacher's and pupils' actions. Retain the actual source
        # reinforcement steps as well as the lesson-specific success evidence.
        result["PENTAKSIRAN"] = (p["Reinforcement / PBD"] +
                                 "\nEvidence: " + meta["pbd evidence"])
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
    # A template may provide reflection placeholders, but teacher-entered
    # reflection must never be replaced by a source template.
    if not str(rows.get("REFLEKSI") or "").strip():
        result["REFLEKSI"] = meta.get("teacher reflection", "")
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
