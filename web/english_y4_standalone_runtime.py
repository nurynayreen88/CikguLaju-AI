"""Opt-in runtime bridge: use existing Year 4 standalone RPH for selected Lesson.

Does not alter database, source lesson files, or other subjects/years.
"""
import re
from english_standalone_adapter import get_english_rph


def install(runtime):
    original = getattr(runtime, "_local_rph_text", None)
    year_number = getattr(runtime, "_english_primary_year_number_v2517", None)
    if not callable(original) or not callable(year_number):
        return False

    def specific_rph(state):
        if not isinstance(state, dict):
            return original(state)
        subject = re.sub(r"[^a-z]", "", str(state.get("subject") or "").casefold())
        if subject not in ("english", "bahasainggeris", "bi"):
            return original(state)
        if year_number(state.get("year")) != 4:
            return original(state)
        lesson = state.get("lesson_no") or state.get("textbook_lesson_no") or state.get("lesson")
        if not lesson:
            return original(state)
        standalone = get_english_rph(4, "English", lesson)
        if standalone is None:
            return original(state)
        # Never expose internal verification ledgers in teacher-facing material.
        standalone = re.split(r"(?im)^##\s*(?:Verified mapping and limits|Source verification|QA notes)\s*$", standalone, maxsplit=1)[0]
        standalone = re.sub(r"(?im)^\*\*(?:Status|QA status|Internal review):\*\*.*$", "", standalone)
        standalone = re.sub(r"(?m)^#{1,3}\s+", "", standalone)
        standalone = re.sub(r"\*\*(.*?)\*\*", r"\1", standalone)
        return standalone

    runtime._local_rph_text = specific_rph
    return True


# The older text bridge above does not affect the actual Word/PDF writer:
# both final document generators call runtime._rph_rows(state, ai_text).
# This second, independent bridge updates those rows only for a validated
# English Year 4 SOW Lesson. Other years, subjects, quota and callbacks are
# untouched. Teacher-choice drafts and unapproved sources are not released.
from pathlib import Path
import json

Y4_ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english" / "year4"
OFFICIAL_SOW_INDEX = (Path(__file__).resolve().parents[1] / "audits" /
                      "english_primary_2_6_official_sow_index_20261103.json")
_SOW_INDEX_VERSION = "2026-11-03-source-table-2-6"
_LS_CODE = re.compile(r"(?<!\d)[1-5]\.\d\.\d(?!\d)")
_QA_STATUS = re.compile(r"(?im)^\*\*QA status:\*\*\s*([^\n]+)")
_METADATA = re.compile(r"(?im)^\*\*([^*:\n]{1,70}):\*\*\s*([^\n]+)")
_SECTION = re.compile(r"(?m)^##\s+([^\n]+)\s*$")
_MARKER = re.compile(
    r"(?im)^\*\*(?:SOW(?: reference| source)?|Source(?: mapping| verification)?|"
    r"References|Resources|Audio(?: source| file integrity)?|"
    r"Workbook|Differentiation|QA status):\*\*"
)


def _selected_y4_lesson(state):
    if not isinstance(state, dict):
        return None
    subject = re.sub(r"[^a-z]", "", str(state.get("subject") or "").casefold())
    if subject not in ("english", "bahasainggeris", "bi"):
        return None
    year = str(state.get("year") or state.get("year_label") or "").strip().casefold()
    if year not in ("4", "year 4", "tahun 4", "primary year 4", "y4", "tahun 4 (sk)"):
        return None
    # Do not infer a lesson from the RPT row ID or a school week.
    value = state.get("lesson_no") or state.get("textbook_lesson_no") or state.get("lesson")
    if isinstance(value, bool):
        return None
    value = str(value or "").strip()
    if not value.isascii() or not value.isdecimal():
        return None
    number = int(value)
    return number if 1 <= number <= 160 else None


def _sow_record(number, index_path=OFFICIAL_SOW_INDEX):
    try:
        index = json.loads(Path(index_path).read_text(encoding="utf-8"))
        if index.get("version") != _SOW_INDEX_VERSION:
            return None
        lessons = index.get("lessons") or {}
        if sum(key.startswith("4/") for key in lessons) != 160:
            return None
        entry = lessons.get("4/%d" % number)
        if (not isinstance(entry, dict) or entry.get("n") != number
                or entry.get("teacher_selected") is not False):
            return None
        main, comp = entry.get("main_ls"), entry.get("complementary_ls")
        if not isinstance(main, str) or not isinstance(comp, str):
            return None
        if not _LS_CODE.fullmatch(main) or not _LS_CODE.fullmatch(comp):
            return None
        return entry
    except (OSError, ValueError, TypeError):
        return None


def _plain(text):
    """Preserve lesson-specific teacher/pupil actions; omit Markdown syntax."""
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", str(text).strip())
    text = re.sub(r"(?m)^\s*[-*]\s+", "• ", text)
    return text.strip()


def _metadata(text):
    return {match.group(1).strip().casefold(): match.group(2).strip()
            for match in _METADATA.finditer(text)}


def _phase_sections(text):
    matches = list(_SECTION.finditer(text))
    parsed = {}
    for i, match in enumerate(matches):
        title = match.group(1).strip().casefold()
        body = text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        # The last closure section often continues into source and audit notes.
        marker = _MARKER.search(body)
        if marker:
            body = body[:marker.start()]
        body = _plain(body)
        if not body:
            continue
        if title.startswith("set induction"):
            parsed["induction"] = body
        elif re.match(r"^activity\s+[123]\b", title):
            number = re.match(r"^activity\s+([123])\b", title).group(1)
            parsed["activity" + number] = body
        elif "pbd" in title or "reinforcement" in title or title.startswith("assessment"):
            parsed["pbd"] = body
        elif title.startswith("closure"):
            parsed["closure"] = body
        elif title.startswith("differentiation"):
            parsed["differentiation"] = body
    return parsed


def load_release_candidate(number, *, root=Y4_ROOT, index_path=OFFICIAL_SOW_INDEX):
    """Return content for a matching, provisionally reviewed fixed-SOW lesson.

    READY — provisional does NOT imply final teacher approval or verified
    audio delivery; never promote any QA status. DRAF/NOT READY remains gated.
    """
    if type(number) is not int or not 1 <= number <= 160:
        return None
    source = _sow_record(number, index_path)
    if source is None:
        return None
    try:
        raw = (Path(root) / ("lesson_%03d.md" % number)).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if not re.search(r"(?im)^# English Year 4\s+[—-]\s+Lesson\s*0*" +
                     str(number) + r"\b", raw):
        return None
    status = _QA_STATUS.search(raw)
    if not status or not status.group(1).strip().upper().startswith("READY"):
        return None
    if "NOT READY" in status.group(1).upper() or "DRAF" in status.group(1).upper():
        return None
    clean_source = raw[:status.start()]
    header = clean_source.split("\n## ", 1)[0]
    meta = _metadata(header)
    main = meta.get("main sk/sp") or meta.get("main sp") or ""
    comp = meta.get("complementary sk/sp") or meta.get("complementary sp") or ""
    main_codes, comp_codes = _LS_CODE.findall(main), _LS_CODE.findall(comp)
    if main_codes != [source["main_ls"]] or comp_codes != [source["complementary_ls"]]:
        return None
    sections = _phase_sections(clean_source)
    required = ("induction", "activity1", "activity2", "pbd", "closure")
    if not all(sections.get(k) for k in required):
        return None
    if not all("Teacher:" in sections[k] and "Pupils:" in sections[k]
               for k in ("induction", "activity1", "activity2", "closure")):
        return None
    return {"sow": source, "meta": meta, "sections": sections}


def _materials(meta):
    text = (meta.get("materials") or meta.get("references")
            or meta.get("resources") or "").strip()
    # These are audit-draft file paths, not released classroom resources.
    text = re.sub(r"(?:^|[;\s])resources/[^\s;,]+(?:\.md)?", "", text, flags=re.I)
    text = re.sub(r"\s*;\s*;", ";", text).strip(" ;,")
    audio = (meta.get("audio") or "").strip()
    if audio and not re.search(r"pending|unverified|requires|draft|not verified", audio, re.I):
        text = (text + "; " + audio).strip(" ;")
    return _plain(text)


def adapt_rows(state, rows, *, root=Y4_ROOT, index_path=OFFICIAL_SOW_INDEX):
    """Modify only validated Year 4 lesson fields used by Telegram Word/PDF."""
    number = _selected_y4_lesson(state)
    if number is None or not isinstance(rows, dict):
        return rows
    item = load_release_candidate(number, root=root, index_path=index_path)
    if item is None:
        return rows
    sow, meta, steps = item["sow"], item["meta"], item["sections"]
    for field, standard in (("sp_code", sow["main_ls"]),
                            ("bi_main_sp_code", sow["main_ls"]),
                            ("comp_sp_code", sow["complementary_ls"]),
                            ("bi_comp_sp_code", sow["complementary_ls"])):
        selected = str(state.get(field) or "").strip()
        if selected and selected != standard:
            return rows

    result = dict(rows)
    main_cs = sow["main_ls"].rsplit(".", 1)[0]
    comp_cs = sow["complementary_ls"].rsplit(".", 1)[0]
    result["MAIN CONTENT STANDARD"] = main_cs
    result["MAIN LEARNING STANDARD"] = sow["main_ls"]
    result["COMPLEMENTARY CONTENT STANDARD"] = comp_cs
    result["COMPLEMENTARY LEARNING STANDARD"] = sow["complementary_ls"]
    result["STANDARD KANDUNGAN"] = "Main: %s; Complementary: %s" % (main_cs, comp_cs)
    result["STANDARD PEMBELAJARAN"] = "Main: %s; Complementary: %s" % (
        sow["main_ls"], sow["complementary_ls"])
    topic = str(sow.get("topic") or "").strip()
    if topic.lower() in ("teacher to complete", "teacher to select"):
        # This is a CikguLaju suggestion, not an official SOW-fixed topic.
        suggested = (meta.get("topic") or meta.get("unit/topic") or "").strip()
        topic = (suggested + " (suggested topic)") if suggested else topic
    result["TAJUK"] = topic + (" — " + sow["focus"] if sow.get("focus") else "")

    objective = meta.get("learning objectives") or meta.get("learning objective")
    if objective:
        result["OBJEKTIF PEMBELAJARAN"] = _plain(objective)
        result["KRITERIA KEJAYAAN"] = _plain(meta.get("success evidence") or objective)
    materials = _materials(meta)
    if materials:
        result["BAHAN BANTU MENGAJAR"] = materials
    evidence = meta.get("pbd") or meta.get("success evidence") or steps["pbd"]
    result["PENTAKSIRAN"] = _plain(evidence)
    result["SET INDUKSI"] = steps["induction"]
    activities = ["Activity 1\n" + steps["activity1"],
                  "Activity 2\n" + steps["activity2"]]
    if steps.get("activity3"):
        activities.append("Activity 3\n" + steps["activity3"])
    activities.append("Reinforcement / PBD\n" + steps["pbd"])
    result["AKTIVITI UTAMA"] = "\n\n".join(activities)
    result["PENUTUP"] = steps["closure"]
    if steps.get("differentiation"):
        result["PEMULIHAN / PENGAYAAN"] = steps["differentiation"]
    # Only lesson-content fields change. Preserve teacher-entered time, class,
    # attendance, date and the existing credit/entitlement transaction path.
    return result


def install_rows(runtime):
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y4_RPH_ROWS_ACTIVE", False):
        return True
    original = getattr(runtime, "_rph_rows", None)
    if not callable(original):
        return False

    def year4_rows(state, *args, **kwargs):
        rows = original(state, *args, **kwargs)
        try:
            return adapt_rows(state, rows)
        except Exception as exc:
            print("English Y4 Word/PDF verified-row fallback:", repr(exc), flush=True)
            return rows

    runtime._rph_rows = year4_rows
    runtime.CIKGULAJU_ENGLISH_Y4_RPH_ROWS_ACTIVE = True
    return True
