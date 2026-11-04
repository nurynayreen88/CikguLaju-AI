"""Live *suggestion* RPH row bridge for 9 English Year 5 teacher-choice lessons.

This intentionally does not mark DRAF materials READY. Seven Language
Awareness lessons use the existing SOW-referenced textbook activities; two
Project-Based Learning lessons are labelled CikguLaju proposals. No official
CS/LS is invented when the SOW reserves skill selection for the teacher.

Both native Word and PDF take rows from app._rph_rows(). Other years,
subjects, fixed-standard Year 5 lessons, payment state, and callbacks are
unchanged.
"""
import json
from pathlib import Path
import re

from web.english_y5_standalone_runtime import (
    CHOICE_LESSONS, GATE_VERSION, LESSON_ROOT, _gate, _target,
)

PROPOSAL_PATH = LESSON_ROOT / "teacher_choice_proposals_2027.json"
VERSION = "english-y5-9-teacher-choice-proposals-20261104"
PROJECTS = frozenset((88, 160))
_FIXED_PAIR = re.compile(r"(?<!\d)[1-5]\.\d\.\d(?!\d)")
_DRAFT_MARKER = re.compile(r"\b(?:DRAF|draft)\b", re.I)
_LS_PENDING = "Teacher to choose Year 5 DSKP standard (not fixed by SOW)"


def _data(path=PROPOSAL_PATH):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError, TypeError):
        return None
    if (data.get("version") != VERSION or data.get("year") != 5
            or data.get("status") != "CADANGAN_DRAF_TEACHER_TO_CONFIRM_DSKP"):
        return None
    lessons = data.get("lessons")
    if not isinstance(lessons, dict) or set(lessons) != {str(n) for n in CHOICE_LESSONS}:
        return None
    return lessons


def _valid_phase(phase):
    return (isinstance(phase, dict) and type(phase.get("minutes")) is int
            and 1 <= phase["minutes"] <= 45
            and all(isinstance(phase.get(k), str) and
                    15 <= len(phase[k].strip()) <= 550
                    for k in ("teacher", "pupils")))


def load_proposal(number, *, root=LESSON_ROOT, proposal_path=PROPOSAL_PATH):
    if type(number) is not int or number not in CHOICE_LESSONS:
        return None
    sow = _gate(root)
    if not isinstance(sow, dict):
        return None
    record = sow.get(str(number))
    if (not isinstance(record, dict)
            or record.get("teacher_choice") is not True
            or record.get("main_ls") is not None
            or record.get("complementary_ls") is not None):
        return None
    data = _data(proposal_path)
    if data is None:
        return None
    proposal = data.get(str(number))
    if not isinstance(proposal, dict):
        return None
    required = ("kind", "topic", "materials", "objective", "criteria",
                "source_marker", "differentiation")
    if not all(isinstance(proposal.get(key), str) and
               len(proposal[key].strip()) >= 8 for key in required):
        return None
    kind = proposal["kind"]
    if number in PROJECTS:
        if not kind.startswith("Project-Based Learning"):
            return None
    elif not kind.startswith("Language Awareness"):
        return None
    if any(_FIXED_PAIR.search(proposal[key]) for key in required):
        # This lesson has no official fixed CS/LS. A proposal must not
        # smuggle an invented official learning-standard code into Word/PDF.
        return None
    phases = proposal.get("phases")
    if not isinstance(phases, list) or not 3 <= len(phases) <= 5:
        return None
    if any(not _valid_phase(p) for p in phases):
        return None
    if phases[0].get("label") != "Set Induction":
        return None
    if any(phase.get("label") != "Activity %d" % i
           for i, phase in enumerate(phases[1:], 1)):
        return None
    pbd, closure = proposal.get("pbd"), proposal.get("closure")
    if not _valid_phase(pbd) or not _valid_phase(closure):
        return None
    if sum(p["minutes"] for p in phases) + pbd["minutes"] + closure["minutes"] != 60:
        return None

    try:
        text = (Path(root) / ("lesson_%03d.md" % number)).read_text(
            encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if not re.search(r"(?im)^# [^\n]*\bLesson\s+0*%d\b" % number, text):
        return None
    if not _DRAFT_MARKER.search(text):
        return None
    if proposal["source_marker"].casefold() not in text.casefold():
        return None
    if number in PROJECTS:
        if not re.search(r"(?i)(?:teacher.{0,45}select|CikguLaju.{0,30}suggestion|teacher approval)", text):
            return None
    return proposal


def _phase_text(phase):
    return ("Teacher: %s\nPupils: %s" %
            (phase["teacher"].strip(), phase["pupils"].strip()))


def adapt_rows(state, rows, *, root=LESSON_ROOT, proposal_path=PROPOSAL_PATH):
    number = _target(state)
    if number not in CHOICE_LESSONS or not isinstance(rows, dict):
        return rows
    if isinstance(state, dict) and state.get("task") and str(state["task"]).casefold() != "rph":
        return rows
    proposal = load_proposal(number, root=root, proposal_path=proposal_path)
    if proposal is None:
        return rows

    result = dict(rows)
    result["TAJUK"] = "CADANGAN CIKGULAJU (DRAF) — " + proposal["topic"]
    # Explicitly replace any inherited legacy codes, not assert false
    # authoritative standards for teacher-choice SOW lessons.
    result["MAIN CONTENT STANDARD"] = _LS_PENDING
    result["MAIN LEARNING STANDARD"] = _LS_PENDING
    result["COMPLEMENTARY CONTENT STANDARD"] = _LS_PENDING
    result["COMPLEMENTARY LEARNING STANDARD"] = _LS_PENDING
    result["STANDARD KANDUNGAN"] = _LS_PENDING
    result["STANDARD PEMBELAJARAN"] = _LS_PENDING
    result["OBJEKTIF PEMBELAJARAN"] = "Suggested: " + proposal["objective"]
    result["KRITERIA KEJAYAAN"] = "Suggested evidence: " + proposal["criteria"]
    result["BAHAN BANTU MENGAJAR"] = proposal["materials"]
    result["SET INDUKSI"] = ("%d minutes\n" % proposal["phases"][0]["minutes"] +
                             _phase_text(proposal["phases"][0]))
    result["AKTIVITI UTAMA"] = "\n\n".join(
        "%s (%d minutes)\n%s" %
        (p["label"], p["minutes"], _phase_text(p)) for p in proposal["phases"][1:])
    result["PENTAKSIRAN"] = ("PBD (%d minutes)\n%s" %
                             (proposal["pbd"]["minutes"], _phase_text(proposal["pbd"])))
    result["PENUTUP"] = ("%d minutes\n" % proposal["closure"]["minutes"] +
                         _phase_text(proposal["closure"]))
    result["PEMULIHAN / PENGAYAAN"] = proposal["differentiation"]
    # Keep teacher-entered date/time/class/attendance/reflection, existing
    # entitlement checks and all other state fields from the original rows.
    return result


def install(runtime):
    """Install the nine clearly labelled draft proposals without unlocking 151 fixed lessons."""
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y5_CHOICE_PROPOSALS_ACTIVE", False):
        return True
    original = getattr(runtime, "_rph_rows", None)
    if not callable(original):
        return False

    def year5_choice_rows(state, *args, **kwargs):
        rows = original(state, *args, **kwargs)
        try:
            return adapt_rows(state, rows)
        except Exception as exc:
            print("English Y5 teacher-choice proposal fallback:", repr(exc), flush=True)
            return rows

    runtime._rph_rows = year5_choice_rows
    runtime.CIKGULAJU_ENGLISH_Y5_CHOICE_PROPOSALS_ACTIVE = True
    return True
