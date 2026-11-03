"""Fail-closed English Year 5 standalone RPH bridge for the existing Telegram row renderer.

This module never changes DB records, credits, callbacks, or other subjects/years.
The 160 source files are DRAF, so installation is opt-in via env flag and is not
equivalent to curriculum/printed-page/audio/A4 or teacher approval.
"""
import json
import os
from pathlib import Path
import re

LESSON_ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english" / "year5"
GATE_VERSION = "y5-official-sow-20261103"
CHOICE_LESSONS = frozenset((16, 34, 52, 70, 88, 106, 124, 142, 160))
RELEASE_FLAG = "CIKGULAJU_Y5_DRAFT_RPH_ENABLED"
_SECTION = re.compile(
    r"^(Set induction|Activity [123]\b|Main activities|PBD and closure|"
    r"Assessment and closure|Reinforcement\s*/\s*PBD|PBD\b|Assessment\b|"
    r"Closure\b|Differentiation\b)", re.I)
_STOP = re.compile(
    r"^(?:QA(?: status| note)?|Status|Verification|Workbook(?: practice| link)?|Audio|"
    r"Source(?: rule| verification)?|Teacher reflection|Reflection|"
    r"Non-textbook source rule|Final check|Materials)(?:\s*\([^)]*\))?\s*:", re.I)
_LS = re.compile(r"(?<!\d)[1-5]\.\d\.\d(?!\d)")
_STRIP = re.compile(r"\*\*(.*?)\*\*")


def _target(state):
    if not isinstance(state, dict):
        return None
    subject = re.sub(r"[^a-z]", "", str(state.get("subject") or "").casefold())
    if subject not in ("english", "bahasainggeris", "bi"):
        return None
    year = str(state.get("year") or state.get("year_label") or "").strip().casefold()
    if year not in ("5", "tahun 5", "year 5", "primary year 5", "y5", "tahun 5 (sk)"):
        return None
    raw = state.get("lesson_no") or state.get("textbook_lesson_no") or state.get("lesson")
    if isinstance(raw, bool):
        return None
    raw = str(raw or "").strip()
    if not raw.isascii() or not raw.isdecimal():
        return None
    number = int(raw)
    return number if 1 <= number <= 160 else None


def _plain(line):
    line = re.sub(r"^\s*#{1,4}\s*", "", line)
    line = re.sub(r"^\s*\d+\.\s+", "", line)
    line = _STRIP.sub(r"\1", line)
    return line.strip()


def _field(text, names):
    for name in names:
        match = re.search(r"(?im)\b" + re.escape(name) +
                          r"(?:\s*\([^\n)]{1,80}\))?\s*:\s*([^\r\n]+)", text)
        if match:
            result = _plain(match.group(1))
            if result:
                return result
    return ""


def _sections(text):
    parts = {}
    current = None
    for raw in text.splitlines():
        line = _plain(raw)
        found = _SECTION.match(line)
        if found:
            label = found.group(1).casefold()
            if label.startswith("set induction"):
                current = "intro"
            elif label.startswith("activity"):
                current = "activity" + label.split()[1]
            elif label == "main activities":
                current = "main"
            elif "and closure" in label:
                current = "combined"
            elif "pbd" in label or label == "assessment":
                current = "pbd"
            elif label == "closure":
                current = "closure"
            elif label == "differentiation":
                current = "differentiation"
            text_part = line.split(":", 1)[1].strip() if ":" in line else ""
            if text_part:
                parts.setdefault(current, []).append(text_part)
            continue
        if _STOP.match(line):
            current = None
        if current is not None and line:
            parts.setdefault(current, []).append(line)
    return {name: "\n".join(value).strip() for name, value in parts.items()}


def _gate(root):
    try:
        obj = json.loads((Path(root) / "sow_standard_gate_2027.json").read_text(encoding="utf-8"))
        if obj.get("version") != GATE_VERSION or obj.get("fixed_standard_lessons") != 151:
            return None
        if set(obj.get("teacher_selected_lessons") or ()) != CHOICE_LESSONS:
            return None
        if len(obj.get("lessons") or {}) != 160:
            return None
        return obj["lessons"]
    except (OSError, ValueError, TypeError, KeyError):
        return None


def load_lesson(number, *, root=LESSON_ROOT):
    if type(number) is not int or number not in range(1, 161):
        return None
    try:
        text = (Path(root) / ("lesson_%03d.md" % number)).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if not re.search(r"(?i)\bLesson\s+0*%d\b" % number, text.splitlines()[0]):
        return None
    clean = "\n".join(_plain(line) for line in text.splitlines())
    blocks = _sections(text)
    intro = blocks.get("intro")
    activities = [blocks.get("activity%d" % k) for k in (1, 2, 3)]
    main = blocks.get("main")
    if sum(bool(part) for part in activities) >= 2:
        activity = "\n\n".join("Activity %d\n%s" % (idx, step)
                               for idx, step in enumerate(activities, 1) if step)
    else:
        activity = main or ""
    pbd = blocks.get("pbd") or blocks.get("combined") or _field(clean, ("PBD evidence", "PBD"))
    closure = blocks.get("closure") or blocks.get("combined") or ""
    materials = _field(clean, ("Materials", "Sources", "References"))
    objective = _field(clean, ("Suggested learning objectives", "Suggested objectives", "Learning objectives",
                               "Learning objective", "Objectives", "Objective"))
    if not all((intro, activity, pbd, closure, materials, objective)):
        return None
    before = re.split(r"(?im)^\s*(?:\d+\.\s*)?(?:\*\*)?Set induction\b", text, maxsplit=1)[0]
    # Only codes in source metadata/header count, not unrelated examples in later tasks.
    codes = frozenset(_LS.findall(before))
    return {"source_codes": codes, "materials": materials, "objective": objective,
            "intro": intro, "activities": activity, "pbd": pbd, "closure": closure,
            "differentiation": blocks.get("differentiation") or ""}


def adapt_rows(state, rows, *, root=LESSON_ROOT):
    number = _target(state)
    if number is None or not isinstance(rows, dict):
        return rows
    sow = _gate(root)
    if sow is None:
        return rows
    expected = sow.get(str(number))
    if not isinstance(expected, dict) or expected.get("teacher_choice") or number in CHOICE_LESSONS:
        # Teacher must select and approve standards; do not invent fixed SOW codes.
        return rows
    main, complementary = expected.get("main_ls"), expected.get("complementary_ls")
    if not isinstance(main, str) or not isinstance(complementary, str):
        return rows
    selected = str(state.get("sp_code") or state.get("learning_standard") or "").strip()
    if selected and selected not in (main, complementary, main.rsplit(".", 1)[0] + "/" + main):
        return rows
    lesson = load_lesson(number, root=root)
    if lesson is None or not {main, complementary}.issubset(lesson["source_codes"]):
        return rows
    # Explicitly retain SOW table / Appendix 1 discrepancy until a source decision.
    if number == 141:
        return rows
    out = dict(rows)
    out["STANDARD KANDUNGAN"] = ("Main: %s; Complementary: %s" %
                                 (main.rsplit(".", 1)[0], complementary.rsplit(".", 1)[0]))
    out["STANDARD PEMBELAJARAN"] = "Main: %s; Complementary: %s" % (main, complementary)
    out["OBJEKTIF PEMBELAJARAN"] = lesson["objective"]
    out["KRITERIA KEJAYAAN"] = lesson["objective"]
    out["BAHAN BANTU MENGAJAR"] = lesson["materials"]
    out["SET INDUKSI"] = lesson["intro"]
    out["AKTIVITI UTAMA"] = lesson["activities"]
    out["PENTAKSIRAN"] = lesson["pbd"]
    out["PENUTUP"] = lesson["closure"]
    if lesson["differentiation"]:
        out["PEMULIHAN / PENGAYAAN"] = lesson["differentiation"]
    return out


def install(runtime, *, enabled=None):
    """Opt-in wrapping of existing Word/PDF row source only; all quotas stay upstream."""
    if enabled is None:
        enabled = os.environ.get(RELEASE_FLAG) == "1"
    if not enabled:
        return False
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y5_DRAFT_RPH_ACTIVE", False):
        return True
    original = getattr(runtime, "_rph_rows", None)
    if not callable(original):
        return False

    def year5_rows(state, *args, **kwargs):
        rows = original(state, *args, **kwargs)
        try:
            return adapt_rows(state, rows)
        except Exception as exc:
            print("English Year 5 RPH gate fallback:", repr(exc), flush=True)
            return rows

    runtime._rph_rows = year5_rows
    runtime.CIKGULAJU_ENGLISH_Y5_DRAFT_RPH_ACTIVE = True
    return True
