"""Attach official SOW Main/Complementary standards to English Y2/Y3 Word/PDF rows.

Existing in-app standalone renderers already supply activities and assessments.
This adapter only fills the metadata they used to leave from older RPHs.
It requires exact source-file identity and exact, matched SOW pairs. Does not
change enrollment, credit, Telegram download routing, or older source files.
"""
from functools import lru_cache
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOW_INDEX = ROOT / "audits" / "english_primary_2_6_official_sow_index_20261103.json"
SOW_VERSION = "2026-11-03-source-table-2-6"
_LS = re.compile(r"(?<!\d)[1-5]\.\d\.\d(?!\d)")
_HEADER_META = re.compile(r"(?im)^\*\*([^*\n]{2,100}):\*\*\s*([^\n]+)")


def _year_and_lesson(state):
    if not isinstance(state, dict):
        return None
    subject = re.sub(r"[^a-z]", "", str(state.get("subject") or "").casefold())
    if subject not in ("english", "bahasainggeris", "bi"):
        return None
    value = str(state.get("year") or state.get("year_label") or "").strip().casefold()
    if value in ("2", "year 2", "tahun 2", "y2"):
        year = 2
    elif value in ("3", "year 3", "tahun 3", "y3"):
        year = 3
    else:
        return None
    raw = state.get("lesson_no")
    if raw is None or raw == "":
        raw = state.get("textbook_lesson_no")
    if raw is None or raw == "":
        raw = state.get("lesson")
    if type(raw) is int:
        number = raw
    elif isinstance(raw, str) and raw.strip().isascii() and raw.strip().isdecimal():
        number = int(raw.strip())
    else:
        return None
    if not 1 <= number <= 160:
        return None
    return year, number


@lru_cache(maxsize=1)
def _sow_index():
    try:
        value = json.loads(SOW_INDEX.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    if value.get("version") != SOW_VERSION:
        return {}
    lessons = value.get("lessons")
    if not isinstance(lessons, dict):
        return {}
    if any(sum(key.startswith(str(year) + "/") for key in lessons) != 160
           for year in (2, 3)):
        return {}
    return lessons


def _source_record(year, number):
    path = ROOT / "rph_standalone" / "english" / ("year%d" % year) / (
        "lesson_%03d.md" % number)
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if not re.search(r"(?im)^# English Year %d\s*[—-]\s*Lesson\s*0*%d\b" %
                     (year, number), source):
        return None
    header = source.split("\n## ", 1)[0]
    meta = {m.group(1).strip().lower(): m.group(2).strip()
            for m in _HEADER_META.finditer(header)}
    def find_code(prefix):
        for k, value in meta.items():
            if k.startswith(prefix):
                matches = _LS.findall(value)
                if matches:
                    return matches[-1]
        return None
    return meta, find_code("main sk/sp"), find_code("complementary sk/sp"), source



def _source_task_objective(source):
    """Derive a learning goal from a real pupil action in the source Lesson.

    Do not claim a new official source reference, workbook page or threshold.
    Earlier Y3 lesson files mostly lack explicit objective header metadata.
    """
    phases = list(re.finditer(r"(?m)^##\s+([^\n]+)\n", source))
    activities = []
    for i, match in enumerate(phases):
        title = match.group(1).strip().casefold()
        if not (title.startswith("activity 2") or title.startswith("activity 1")):
            continue
        end = phases[i + 1].start() if i + 1 < len(phases) else len(source)
        activities.append((0 if title.startswith("activity 2") else 1,
                           source[match.end():end]))
    for _, body in sorted(activities):
        cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", body)
        pupil = re.search(r"\bPupils?\s*:\s*([^.\n]{22,230})", cleaned, re.I)
        if not pupil:
            pupil = re.search(r"\bPupils?\s+([a-z][^.\n]{22,230})", cleaned)
        if not pupil:
            continue
        action = pupil.group(1).strip(" .;:\u2013-")
        if not 22 <= len(action) <= 230:
            continue
        if re.search(r"referenced tasks|main and complementary skills|summarise (?:one thing|their learning)|activities? as directed", action, re.I):
            continue
        if re.search(r"pending|unverified|not ready|QA status|teacher approval", action, re.I):
            continue
        action = action[0].lower() + action[1:]
        return "By the end of the lesson, pupils can " + action.rstrip(".") + "."
    return None


def enrich_rows(state, rows):
    match = _year_and_lesson(state)
    if match is None or not isinstance(rows, dict):
        return rows
    year, number = match
    # Require that the previous source-to-document step really installed
    # the expected standalone lesson; don't label AI fallback as reviewed.
    expected_path = "rph_standalone/english/year%d/lesson_%03d.md" % (year, number)
    if rows.get("_standalone_y%d_source" % year) != expected_path:
        return rows
    sow = _sow_index().get("%d/%d" % (year, number))
    source = _source_record(year, number)
    if not sow or sow.get("teacher_selected") or source is None:
        return rows
    meta, main, comp, raw_source = source
    if main != sow.get("main_ls") or comp != sow.get("complementary_ls"):
        return rows
    # Fail closed if the teacher selected standards other than this Lesson's.
    for key, expected in (("sp_code", main), ("bi_main_sp_code", main),
                          ("comp_sp_code", comp), ("bi_comp_sp_code", comp)):
        selected = str(state.get(key) or "").strip()
        if selected and selected != expected:
            return rows
    out = dict(rows)
    out.update({
        "MAIN CONTENT STANDARD": main.rsplit(".", 1)[0],
        "MAIN LEARNING STANDARD": main,
        "COMPLEMENTARY CONTENT STANDARD": comp.rsplit(".", 1)[0],
        "COMPLEMENTARY LEARNING STANDARD": comp,
        "STANDARD KANDUNGAN": "Main: %s; Complementary: %s" %
                             (main.rsplit(".", 1)[0], comp.rsplit(".", 1)[0]),
        "STANDARD PEMBELAJARAN": "Main: %s; Complementary: %s" % (main, comp),
    })
    if sow.get("topic") not in ("teacher to complete", "teacher to select"):
        focus = sow.get("focus") or ""
        out["TAJUK"] = str(sow["topic"]) + (" — " + focus if focus else "")
    for field, aliases in (
        ("OBJEKTIF PEMBELAJARAN", ("learning objectives", "learning objective", "objective", "objectives")),
        ("KRITERIA KEJAYAAN", ("success criteria", "success evidence")),
    ):
        for alias in aliases:
            if alias in meta and meta[alias].strip():
                out[field] = re.sub(r"\*\*([^*]+)\*\*", r"\1", meta[alias]).strip()
                break
    # Earlier Year 3 standalone RPH may omit Objective metadata despite
    # providing explicit pupil tasks. Prefer a direct task-derived objective
    # over leaving the previous generic objective in the native document.
    if out.get("OBJEKTIF PEMBELAJARAN") == rows.get("OBJEKTIF PEMBELAJARAN"):
        objective = _source_task_objective(raw_source)
        if objective:
            out["OBJEKTIF PEMBELAJARAN"] = objective
            if not meta.get("success criteria") and not meta.get("success evidence"):
                out["KRITERIA KEJAYAAN"] = "Evidence: " + objective.removeprefix(
                    "By the end of the lesson, pupils can ")
    return out


def install(runtime):
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y2_Y3_SOW_FIELDS_ACTIVE", False):
        return True
    previous = getattr(runtime, "_rph_rows", None)
    if not callable(previous):
        return False

    def english_y2_y3_rows(state, *args, **kwargs):
        rows = previous(state, *args, **kwargs)
        try:
            return enrich_rows(state, rows)
        except Exception as exc:
            print("English Y2/Y3 SOW metadata bridge fallback:", repr(exc), flush=True)
            return rows

    runtime._rph_rows = english_y2_y3_rows
    runtime.CIKGULAJU_ENGLISH_Y2_Y3_SOW_FIELDS_ACTIVE = True
    return True
