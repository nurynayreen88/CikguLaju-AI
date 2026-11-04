"""English Year 4 remaining 11 provisional Word/PDF lesson plans.

10 teacher-choice Language Awareness / Project-Based Learning lessons have no
SOW-prescribed fixed SK/SP. Lesson 30 has a genuine TB/SOW audio conflict.
Expose *clearly labelled draft previews* from existing source activities,
never mark approved or claim that CD1 Track 29 equals CD2 Track 29.
"""
import re

from web.english_y4_standalone_runtime import (
    Y4_ROOT, OFFICIAL_SOW_INDEX, _selected_y4_lesson, _sow_record,
    _phase_sections, _metadata, _materials, _plain, load_release_candidate,
)
from pathlib import Path
import json

CHOICES = frozenset((16, 32, 48, 64, 80, 96, 112, 128, 144, 160))
AUDIO_CONFLICT = 30
PENDING = CHOICES | {AUDIO_CONFLICT}
TEACHER_STANDARD = "Teacher to select Year 4 DSKP standard (not fixed by SOW)"
_SOURCE_LINE = re.compile(r"(?m)^# English Year 4\s+[—-]\s+Lesson\s*0*(\d+)\b")
_STATUS = re.compile(r"(?im)^\*\*QA status:\*\*\s*(.+)")
_CODES = re.compile(r"(?<!\d)[1-5]\.\d\.\d(?!\d)")

# Two specific CikguLaju proposals; never claim these are official SOW tasks.
PROJECTS = {
    80: {
        "name": "The King of Kites — Story Values Display (CikguLaju suggested project)",
        "objective": "Create a group display illustrating two values from The King of Kites and explain one text-based reason for each value",
        "criteria": "Two illustrated values, two event-based reasons, one short group explanation and one peer-response correction",
        "materials": "The King of Kites story already studied in Lesson 79; teacher-created character/value cards, A4 poster paper and drawing tools. No prescribed workbook or audio.",
        "intro": "Teacher: Recall a significant choice made by a character in The King of Kites.\nPupils: Name one event and one value shown in the story.",
        "act1": "Activity 1 (15 minutes)\nTeacher: Guide groups to select two story values and find an event that supports each; allocate roles.\nPupils: Agree on two values, identify supporting events, and share research/drawing/writing roles.",
        "act2": "Activity 2 (20 minutes)\nTeacher: Provide a display template and check the links between values and text-based events.\nPupils: Draw two story scenes, caption each with the value it shows, and explain the event supporting it.",
        "pbd": "Teacher: Check two values and their supporting story events, individual group contributions and a short oral explanation.\nPupils: Present the display, answer a relevant question and correct one unsupported claim.",
        "closure": "Teacher: Invite a practical class application of one story value.\nPupils: State a value and an action that demonstrates it.",
    },
    160: {
        "name": "Healthy Habits Help Desk (CikguLaju suggested project)",
        "objective": "Prepare a simple illustrated healthy-habits advice poster and explain two relevant practical suggestions",
        "criteria": "A labelled poster, two accurate advice statements, one short role-play explanation and a relevant answer to a peer question",
        "materials": "Familiar What’s the matter? language from Lessons 157–159; picture cards of everyday situations, A4 poster paper, markers. No prescribed workbook or audio.",
        "intro": "Teacher: Recall 'What's the matter?' language and everyday healthy choices.\nPupils: Name a familiar health-related situation and useful response.",
        "act1": "Activity 1 (15 minutes)\nTeacher: Organise groups to select a safe everyday scenario and choose two suitable advice statements.\nPupils: Plan the poster, assign roles and rehearse two helpful advice sentences.",
        "act2": "Activity 2 (20 minutes)\nTeacher: Monitor poster language and model a brief help-desk role-play.\nPupils: Illustrate the scenario, label their advice and practise explaining the poster to another group.",
        "pbd": "Teacher: Check two relevant advice sentences and observe each pupil's contribution and response to a question.\nPupils: Present a 30-second help-desk role-play, answer a question and correct one unclear sentence.",
        "closure": "Teacher: Revisit one appropriate, everyday healthy choice.\nPupils: Share one useful piece of advice and one improvement to the poster.",
    },
}


# Objectives are *suggested*, anchored in the actual existing RPH tasks;
# never claim they are prescribed learning objectives or fixed SOW LS.
REVIEW_OBJECTIVES = {
    16: ("Complete Unit 1 Revision Activities 1–3, review countries and free-time language, and identify one personal learning target",
         "Revision answers, one corrected item, and a completed Unit 1 self-assessment"),
    32: ("Complete Unit 2 Revision Activities 1–2, use housework and timetable language, and identify a priority for practice",
         "Two reviewed tasks, one checked answer and a Unit 2 self-assessment"),
    48: ("Complete Unit 3 Revision Activities 1–3 on past simple language and identify one correction",
         "Revision responses, one corrected past-simple form and a Unit 3 self-assessment"),
    64: ("Complete Unit 4 revision tasks on ordinal numbers, dates and celebrations, and set a specific learning goal",
         "Checked revision answers, one accurate date or ordinal-number response and a Unit 4 review target"),
    96: ("Complete Unit 6 Getting Around revision, correct a recurring language error and set a further practice target",
         "Revision tasks 1–3, one corrected response and the Unit 6 self-assessment"),
    112: ("Complete Unit 7 Helping Out review Activities 1–3, practise a weak language point and choose one learning target",
          "Completed activities, one improved pair response and Unit 7 self-assessment"),
    128: ("Complete Unit 8 Amazing Animals review Activities 1–3, correct an animal-comparison error and set a review target",
          "Reviewed animal vocabulary and comparative responses plus Unit 8 self-assessment"),
    144: ("Complete Unit 9 Get Active review Activities 1–3, correct one language error and select a measurable revision goal",
          "Corrected exercise response, named Unit 9 language target and individual self-assessment"),
}


def _load_pending(number, root, index_path):
    if type(number) is not int or number not in PENDING:
        return None
    sow = _sow_record(number, index_path) if number == AUDIO_CONFLICT else None
    if number == AUDIO_CONFLICT:
        if not sow or (sow["main_ls"], sow["complementary_ls"]) != ("4.3.2", "1.2.5"):
            return None
    else:
        try:
            index = json.loads(Path(index_path).read_text(encoding="utf-8"))
            if index.get("version") != "2026-11-03-source-table-2-6":
                return None
            if sum(k.startswith("4/") for k in index.get("lessons", {})) != 160:
                return None
            sow = index["lessons"].get("4/%d" % number)
            if not sow or sow.get("teacher_selected") is not True:
                return None
            if sow.get("main_ls") is not None or sow.get("complementary_ls") is not None:
                return None
        except (ValueError, TypeError, OSError, KeyError):
            return None
    try:
        raw = (Path(root) / ("lesson_%03d.md" % number)).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = _SOURCE_LINE.search(raw)
    if not match or int(match.group(1)) != number:
        return None
    status = _STATUS.search(raw)
    if not status or not re.search(r"\b(?:DRAF|NOT READY)\b", status.group(1), re.I):
        return None
    header = raw.split("\n## ", 1)[0]
    meta = _metadata(header)
    sections = _phase_sections(raw[:status.start()])
    # Lesson 16 has a full 'Reinforcement / PBD' phase followed by a
    # separate 'PBD and differentiation' summary. The shared phase parser
    # treats both as PBD and overwrites the actual Teacher/Pupils procedure.
    # Retain the original phase, not the later summary, without changing
    # the 149 already reviewed Year 4 lessons.
    if "Teacher:" not in sections.get("pbd", "") or "Pupils:" not in sections.get("pbd", ""):
        match = re.search(r"(?im)^##\s+(?:Reinforcement\s*/\s*PBD|PBD\s*/\s*reinforcement)\b[^\n]*\n", raw)
        if match:
            tail = raw[match.end():]
            next_section = re.search(r"(?m)^##\s+", tail)
            sections["pbd"] = _plain(tail[:next_section.start()] if next_section else tail)
    if not all(sections.get(key) for key in
               ("induction", "activity1", "activity2", "pbd", "closure")):
        return None
    for section in ("induction", "activity1", "activity2", "pbd", "closure"):
        if "Teacher:" not in sections[section] or "Pupils:" not in sections[section]:
            # Source controls can use "Pupil action"; _plain normalises only
            # "Pupils action" while "Pupil action" may remain. Handle below.
            section_text = re.sub(r"(?im)\bPupil action:\s*", "Pupils: ",
                                  sections[section])
            if "Teacher:" not in section_text or "Pupils:" not in section_text:
                return None
            sections[section] = section_text
    if number == AUDIO_CONFLICT:
        main = _CODES.findall(meta.get("main sp", ""))
        comp = _CODES.findall(meta.get("complementary sp", ""))
        if main != ["4.3.2"] or comp != ["1.2.5"]:
            return None
        if "CD1 Track 29" not in raw or "CD2 Track 29" not in raw:
            return None
    return {"sow": sow, "meta": meta, "sections": sections}


def adapt_rows(state, rows, *, root=Y4_ROOT, index_path=OFFICIAL_SOW_INDEX):
    number = _selected_y4_lesson(state)
    if number not in PENDING or not isinstance(rows, dict):
        return rows
    if state.get("task") and str(state.get("task")).strip().casefold() != "rph":
        return rows
    item = _load_pending(number, root, index_path)
    if item is None:
        return rows
    sow, meta, phases = item["sow"], item["meta"], item["sections"]
    if number in CHOICES:
        # These are teacher-selected. Prevent accidental printing of fixed
        # CS/LS from a stale legacy RPH.
        result = dict(rows)
        for key in ("MAIN CONTENT STANDARD", "MAIN LEARNING STANDARD",
                    "COMPLEMENTARY CONTENT STANDARD", "COMPLEMENTARY LEARNING STANDARD",
                    "STANDARD KANDUNGAN", "STANDARD PEMBELAJARAN"):
            result[key] = TEACHER_STANDARD
    else:
        for key, correct in (("sp_code", "4.3.2"),
                             ("bi_main_sp_code", "4.3.2"),
                             ("comp_sp_code", "1.2.5"),
                             ("bi_comp_sp_code", "1.2.5")):
            selected = str(state.get(key) or "").strip()
            if selected and selected != correct:
                return rows
        result = dict(rows)
        result.update({"MAIN CONTENT STANDARD": "4.3",
                       "MAIN LEARNING STANDARD": "4.3.2",
                       "COMPLEMENTARY CONTENT STANDARD": "1.2",
                       "COMPLEMENTARY LEARNING STANDARD": "1.2.5",
                       "STANDARD KANDUNGAN": "Main: 4.3; Complementary: 1.2",
                       "STANDARD PEMBELAJARAN": "Main: 4.3.2; Complementary: 1.2.5"})
    if number in PROJECTS:
        project = PROJECTS[number]
        result["TAJUK"] = "CADANGAN CIKGULAJU (DRAF) — " + project["name"]
        result["OBJEKTIF PEMBELAJARAN"] = "Suggested: " + project["objective"]
        result["KRITERIA KEJAYAAN"] = "Suggested evidence: " + project["criteria"]
        result["BAHAN BANTU MENGAJAR"] = project["materials"]
        result["SET INDUKSI"] = "10 minutes\n" + project["intro"]
        result["AKTIVITI UTAMA"] = project["act1"] + "\n\n" + project["act2"]
        result["PENTAKSIRAN"] = "10 minutes\n" + project["pbd"]
        result["PENUTUP"] = "5 minutes\n" + project["closure"]
        result["PEMULIHAN / PENGAYAAN"] = "Support: picture cues and sentence frames. Extension: independently justify additional story/advice choices."
    else:
        result["TAJUK"] = "DRAF CIKGULAJU (SEMAKAN GURU) — " + str(sow.get("topic") or "")
        if number in REVIEW_OBJECTIVES:
            objective, criteria = REVIEW_OBJECTIVES[number]
            result["OBJEKTIF PEMBELAJARAN"] = "Suggested: " + objective
            result["KRITERIA KEJAYAAN"] = "Suggested evidence: " + criteria
        else:
            result["OBJEKTIF PEMBELAJARAN"] = (
                "Suggested: Write and spell household-chores vocabulary accurately; "
                "check a listening response to TB-prescribed CD1 Track 29 after spoken-content confirmation.")
            result["KRITERIA KEJAYAAN"] = (
                "Evidence: correctly spelled chores and task-specific written "
                "responses; listening evidence only after correct track verification.")
        resources = _materials(meta) or str(meta.get("references") or "SOW unit review")
        resources = re.sub(r"resources/[^\s;,()]+", "", resources, flags=re.I).strip(" ;,")
        if number == AUDIO_CONFLICT:
            resources += ("; AUDIO REFERENCE CONFLICT: printed TB p.39 and SB p.20 "
                          "visually checked — Activity 2 uses CD1 Track 29; "
                          "SOW says CD2 Track 29. MP3s differ; confirm speech before use.")
        result["BAHAN BANTU MENGAJAR"] = resources
        result["SET INDUKSI"] = phases["induction"]
        result["AKTIVITI UTAMA"] = "Activity 1\n%s\n\nActivity 2\n%s" % (
            phases["activity1"], phases["activity2"])
        result["PENTAKSIRAN"] = phases["pbd"]
        result["PENUTUP"] = phases["closure"]
        result["PEMULIHAN / PENGAYAAN"] = (
            "Support: visual prompts, modelling and paired practice. "
            "Extension: independent application and explained corrections.")
    return result


def install(runtime):
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y4_PENDING_DRAFT_PREVIEW_ACTIVE", False):
        return True
    old = getattr(runtime, "_rph_rows", None)
    if not callable(old):
        return False

    def year4_pending_preview(state, *args, **kwargs):
        original = old(state, *args, **kwargs)
        try:
            return adapt_rows(state, original)
        except Exception as exc:
            print("English Y4 pending draft preview fallback:", repr(exc), flush=True)
            return original

    runtime._rph_rows = year4_pending_preview
    runtime.CIKGULAJU_ENGLISH_Y4_PENDING_DRAFT_PREVIEW_ACTIVE = True
    return True
