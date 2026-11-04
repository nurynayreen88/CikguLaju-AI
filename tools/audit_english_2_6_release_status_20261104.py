"""Independent 800-Lesson source-to-native-row QA and release-status inventory.

NOT an automated FINAL READY approval system. This audit proves *technical*
source matching, Word/PDF row coverage, and honest teacher-choice display.
Independent book/audio verification, native PDF Telegram delivery and teacher
sign-off remain separate release blockers.

No app.py import, database writes, production network, Telegram sends, credit
transactions or user modifications. CI uploads a 800-row JSON report.
"""
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from english_y2_standalone_render import apply as year2_rows
from english_y3_standalone_render import apply as year3_rows
from web.english_y2_y3_standard_runtime import enrich_rows as y23_sow
from web.english_y4_standalone_runtime import adapt_rows as y4_fixed
from web.english_y4_pending_draft_preview_runtime import (
    adapt_rows as y4_draft, PENDING as Y4_DRAFT, AUDIO_CONFLICT,
)
from web.english_y5_fixed_draft_preview_runtime import preview_rows as y5_fixed
from web.english_y5_teacher_choice_runtime import adapt_rows as y5_choice
from web.english_y5_standalone_runtime import CHOICE_LESSONS as Y5_CHOICE
from web.english_y6_standalone_runtime import (
    adapt_rows as y6_rows, Y6_TEACHER_CHOICES as Y6_CHOICE,
    TEACHER_SELECTED_STANDARD as Y6_PLACEHOLDER,
)

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_INDEX = ROOT / "audits" / "english_primary_2_6_official_sow_index_20261103.json"
REPORT_PATH = ROOT / "output" / "english_2_6_release_audit_20261104.json"
STATUS_MAPPED = "SOURCE_MAPPING_PASS_FINAL_QA_PENDING"
STATUS_CHOICE = "TEACHER_CHOICE_DRAFT_DSKP_SELECTION_PENDING"
STATUS_CONFLICT = "AUDIO_SOURCE_CONFLICT_DRAFT"
STATUS_FAIL = "TECHNICAL_BLOCKER"
NEEDED = ("TAJUK", "OBJEKTIF PEMBELAJARAN", "SET INDUKSI",
          "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP", "BAHAN BANTU MENGAJAR")
PRESERVE = ("TARIKH", "MASA", "KELAS", "BILANGAN MURID", "REFLEKSI", "KUOTA")

def _base(year):
    return {
        "MATA PELAJARAN": "English", "TAHUN/TINGKATAN": "Year %d" % year,
        "TARIKH": "04/11/2026", "HARI": "Wednesday",
        "MASA": "08:00 - 09:00", "KELAS": "%d Amanah" % year,
        "BILANGAN MURID": "30", "REFLEKSI": "Teacher supplied original notes",
        "KUOTA": 10,
        "TAJUK": "LEGACY GENERIC TOPIC",
        "OBJEKTIF PEMBELAJARAN": "LEGACY GENERIC OBJECTIVE",
        "KRITERIA KEJAYAAN": "LEGACY GENERIC SUCCESS",
        "SET INDUKSI": "LEGACY GENERIC INDUCTION",
        "AKTIVITI UTAMA": "LEGACY GENERIC ACTIVITIES",
        "PENTAKSIRAN": "LEGACY GENERIC ASSESSMENT",
        "PENUTUP": "LEGACY GENERIC CLOSURE",
        "BAHAN BANTU MENGAJAR": "LEGACY GENERIC MATERIALS",
        "MAIN CONTENT STANDARD": "LEGACY MAIN",
        "MAIN LEARNING STANDARD": "LEGACY MAIN",
        "COMPLEMENTARY CONTENT STANDARD": "LEGACY COMP",
        "COMPLEMENTARY LEARNING STANDARD": "LEGACY COMP",
    }


def _render(year, number, record):
    state = {"task": "rph", "subject": "English", "year": "Year %d" % year,
             "lesson_no": number}
    if record["teacher_selected"] is False:
        state["sp_code"] = record["main_ls"]
        state["comp_sp_code"] = record["complementary_ls"]
    baseline = _base(year)
    if year == 2:
        out = y23_sow(state, year2_rows(state, dict(baseline)))
    elif year == 3:
        out = y23_sow(state, year3_rows(state, dict(baseline)))
    elif year == 4:
        out = y4_draft(state, dict(baseline)) if number in Y4_DRAFT else y4_fixed(state, dict(baseline))
    elif year == 5:
        out = y5_choice(state, dict(baseline)) if number in Y5_CHOICE else y5_fixed(state, dict(baseline))
    elif year == 6:
        out = y6_rows(state, dict(baseline))
    else:
        raise ValueError("English Year 2–6 only")
    return out, baseline


def _check(year, number, sow):
    failures = []
    if sow.get("n") != number:
        failures.append("Official SOW Lesson ID mismatch")
    output, baseline = _render(year, number, sow)
    if not isinstance(output, dict):
        return {"year":year,"lesson":number,"status":STATUS_FAIL,
                "failures":["Renderer did not return a dict"]}

    # Teacher-supplied context is not allowed to be replaced by RPH material.
    for key in PRESERVE:
        if output.get(key) != baseline[key]:
            failures.append("Teacher/user data overwritten: " + key)

    for field in NEEDED:
        value = output.get(field)
        if not isinstance(value, str) or not value.strip() or value == baseline[field]:
            failures.append("Missing source-backed document field: " + field)

    for field in ("OBJEKTIF PEMBELAJARAN","AKTIVITI UTAMA","PENTAKSIRAN"):
        if "LEGACY" in str(output.get(field) or ""):
            failures.append("Unreplaced legacy text in " + field)

    category = STATUS_MAPPED
    if year == 4 and number == AUDIO_CONFLICT:
        category = STATUS_CONFLICT
        material = str(output.get("BAHAN BANTU MENGAJAR") or "")
        if ("AUDIO REFERENCE CONFLICT" not in material or
                "CD1" not in material or "CD2" not in material or
                "DRAF" not in str(output.get("TAJUK") or "")):
            failures.append("Y4 Lesson30 audio conflict notice missing")
    elif sow["teacher_selected"]:
        category = STATUS_CHOICE
        for label in ("MAIN CONTENT STANDARD","MAIN LEARNING STANDARD",
                      "COMPLEMENTARY CONTENT STANDARD","COMPLEMENTARY LEARNING STANDARD"):
            value = output.get(label)
            if not isinstance(value,str) or "not fixed by SOW" not in value:
                failures.append("Teacher-choice field improperly asserts official standard: " + label)
        if "DRAF" not in str(output.get("TAJUK") or ""):
            failures.append("Teacher-choice DRAF label missing")
    else:
        for key, expected in (("MAIN LEARNING STANDARD",sow.get("main_ls")),
                              ("COMPLEMENTARY LEARNING STANDARD",sow.get("complementary_ls"))):
            if output.get(key) != expected:
                failures.append("SOW code mismatch in " + key)
        if year == 5 and "DRAF" not in str(output.get("TAJUK") or ""):
            failures.append("Year5 unapproved fixed-source draft label missing")

    return {
        "year":year,"lesson":number,"focus":sow.get("focus"),
        "sow_teacher_selected":sow["teacher_selected"],
        "main_ls":sow.get("main_ls"),"complementary_ls":sow.get("complementary_ls"),
        "status":STATUS_FAIL if failures else category,
        "failures":failures,
        "independent_printed_book_checked":False,
        "independent_audio_content_checked":False,
        "real_teacher_telegram_download_checked":False,
        "final_teacher_approved":False,
    }


def build_report():
    data = json.loads(OFFICIAL_INDEX.read_text(encoding="utf-8"))
    if data.get("version") != "2026-11-03-source-table-2-6" or len(data.get("lessons") or {}) != 800:
        raise RuntimeError("SOW index integrity/version failed")
    rows = []
    for year in range(2,7):
        for number in range(1,161):
            source = data["lessons"].get("%d/%d" % (year,number))
            if not isinstance(source,dict):
                raise RuntimeError("Missing SOW Year%d Lesson%d" % (year,number))
            rows.append(_check(year,number,source))
    counts = Counter(r["status"] for r in rows)
    by_year = {str(year):dict(Counter(r["status"] for r in rows if r["year"]==year))
               for year in range(2,7)}
    return {
        "audit_date":"2026-11-04",
        "source_index_version":data["version"],
        "scope":"Offline Word/PDF shared row contract for 800 English Year 2–6 lessons; does not prove Telegram delivery, external book/audio correctness, or teacher approval.",
        "final_ready_total":0,
        "lesson_total":len(rows),
        "status_counts":dict(counts),
        "by_year":by_year,
        "technical_blocker_lessons":[{"year":r["year"],"lesson":r["lesson"],
                                      "reasons":r["failures"]}
                                     for r in rows if r["status"]==STATUS_FAIL],
        "lessons":rows,
    }


def main():
    report=build_report()
    REPORT_PATH.parent.mkdir(parents=True,exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print("ENGLISH_2_6_800_LESSON_AUDIT",json.dumps(report["status_counts"]),flush=True)
    print("BY_YEAR",json.dumps(report["by_year"]),flush=True)
    if report["technical_blocker_lessons"]:
        for row in report["technical_blocker_lessons"][:30]:
            print("BLOCKED", row,flush=True)
        raise SystemExit("English Word/PDF offline audit found technical blockers")
    expected={STATUS_MAPPED:766,STATUS_CHOICE:33,STATUS_CONFLICT:1}
    if report["status_counts"] != expected:
        raise SystemExit("Unexpected status categories: "+str(report["status_counts"]))
    print("TECHNICAL_800_OF_800_PASS_FINAL_READY_NOT_CLAIMED",flush=True)


if __name__=="__main__":
    main()
