"""Editor-only per-lesson activity-book matching queue for Pendidikan Islam KSSR.

Never infer a printed page from the lesson number, book-text page, or SP code.
Do not use queue items directly in a teacher-facing RPH or a downloads menu.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import json
import re

from pi_activity_book_audit import audit_activity_books

# Public, third-party reading views verified as pointing to KPM-branded covers.
# Cover/source identity != audited edition/pages or right to mirror PDFs.
SOURCE_VIEWERS = {
    2: "https://anyflip.com/lhat/sebp/",
    3: "https://anyflip.com/lhat/dkui/",
}
ORAL_PRIMARY = "ORAL_PRIMARY_NO_FORCED_BOOK"
NEEDS_PAGE = "VERIFY_PAGE_AND_EXERCISE"
NOT_APPLICABLE = "NO_BOOK_CONFIRMATION"
ON_HOLD = "WITHHELD"


def quran_focus(sp):
    """Classify the Quran branch without equating comprehension/tajwid with tasmi'."""
    if re.search(r"1\.6\.", sp):
        return "TAJWID"
    if re.search(r"1\.5\.", sp):
        # Year 2 1.5 is mad asli, not comprehension; use literal SP language.
        return "TAJWID" if "مد اصلي" in sp else "KEFAHAMAN"
    if "مڠحفظ" in sp or re.search(r"1\.[34]\.\d+", sp):
        return "HAFAZAN"
    return "BACAAN"


def candidate_for(row):
    domain = row["domain"]
    sp = row["source_sp"]
    year = row["year"]
    if row["disposition"] == "MUSHAF_PRIMARY_NO_ASSUMED_BA":
        return ORAL_PRIMARY, "TASMI", "Tasmi' al-Quran mesti dinilai melalui bacaan mushaf secara individu."
    if domain == "القرءان":
        skill = quran_focus(sp)
        if skill in ("BACAAN", "HAFAZAN"):
            return ORAL_PRIMARY, skill, (
                "Bacaan/hafazan mesti diperdengarkan; buku aktiviti tidak menggantikan "
                "talaqqi, musyafahah atau pentaksiran lisan."
            )
        if skill == "TAJWID":
            rule = next((s for s in (
                "إظهار حلقي", "إدغام بلا غنة", "إدغام مع الغنة",
                "إخفاء حقيقي", "إقلاب", "مد اصلي", "نون دان ميم شدة"
            ) if s in sp), None)
            return NEEDS_PAGE, "TAJWID", (
                f"Semak latihan mengenal pasti/menandakan hukum {rule or 'tajwid dalam SP'} "
                "pada halaman sebenar, kemudian kekalkan semakan bacaan secara lisan."
            )
        return NEEDS_PAGE, "KEFAHAMAN", (
            "Semak latihan padanan ayat, makna atau pengajaran surah yang disebut dalam SP; "
            "nilai huraian murid dan bukan hafazan bertulis semata-mata."
        )
    if domain == "جاوي":
        can_write = "منوليس" in sp
        can_build = "ممبينا" in sp
        if can_write:
            exercise = "latihan menulis/membaiki ejaan Jawi"
            skill = "TULIS_JAWI"
        elif can_build:
            exercise = "latihan membina perkataan atau ayat Jawi"
            skill = "BINA_JAWI"
        else:
            exercise = "latihan mengenal pasti dan membaca perkataan/teks Jawi"
            skill = "BACA_JAWI"
        return NEEDS_PAGE, skill, (
            f"Semak {exercise} yang betul-betul sepadan SP di Buku Aktiviti Tahun {year}. "
            "Catat halaman bercetak dan arahan asal untuk semakan, bukan kira halaman PDF."
        )
    if domain == "عقيدة":
        return NEEDS_PAGE, "AKIDAH", (
            "Cari latihan padanan maksud/dalil atau kesan keimanan pada topik SP, "
            "kemudian semak justifikasi murid."
        )
    if domain == "عبادة":
        return NEEDS_PAGE, "IBADAH", (
            "Cari latihan tertulis tentang syarat, hukum atau tertib ibadah dalam SP; "
            "jangan menggantikan demonstrasi amali/PBD."
        )
    if domain == "سيرة":
        return NEEDS_PAGE, "SIRAH", (
            "Cari latihan susunan peristiwa, tokoh atau iktibar sirah khusus pada SP; "
            "minta murid memberi sebab atau iktibar."
        )
    if domain == "ادب":
        return NEEDS_PAGE, "ADAB", (
            "Cari latihan situasi dan perlakuan beradab yang tepat pada SP; "
            "susuli dengan pemerhatian amalan murid."
        )
    if domain == "حديث":
        return NEEDS_PAGE, "HADIS", (
            "Cari latihan maksud/pengajaran hadis yang sama dalam SP; "
            "jangan petik atau salin matan yang tidak disahkan."
        )
    raise ValueError(f"Unknown domain {domain!r} for {row['id']}")


def match_queue(root=None):
    a = audit_activity_books() if root is None else audit_activity_books(root=root)
    rows = []
    for row in a["rows"]:
        if row["disposition"] == ON_HOLD:
            continue
        if row["year"] not in SOURCE_VIEWERS:
            # Years 4-6: no compatible KSSR Semakan activity-book source confirmed.
            continue
        disposition, skill, instruction = candidate_for(row)
        sp = row["source_sp"]
        codes = list(dict.fromkeys(re.findall(r"\b[1-9]\.\d+\.\d+\b", sp)))
        priority = (
            "P1_JAWI" if skill.endswith("_JAWI") else
            "P2_SUBJECT" if disposition == NEEDS_PAGE else
            "ORAL_ONLY"
        )
        rows.append({
            "id": row["id"], "year": row["year"],
            "domain": row["domain"], "sp_codes": codes,
            "sp_original": sp,
            "book_candidate": row["book_title_candidate"],
            "book_viewer_reference": SOURCE_VIEWERS[row["year"]],
            "source_evidence": "KPM_BRANDED_COVER_AND_SCHOOL_PORTAL_ONLY",
            "disposition": disposition, "priority": priority,
            "learning_focus": skill,
            "suggested_exercise_to_check": instruction,
            "book_printed_page": None,
            "book_exercise_id": None,
            "exercise_instruction_verified": False,
            "match_to_sp_verified": False,
            "teacher_sentence": None,
            "teacher_material_approved": False,
            "permission_to_mirror_pdf": False,
            "release": "HOLD",
        })
    counts = Counter(r["disposition"] for r in rows)
    focus = Counter(r["learning_focus"] for r in rows)
    year_counts = {
        y: dict(Counter(r["disposition"] for r in rows if r["year"] == y))
        for y in SOURCE_VIEWERS
    }
    assert len(rows) == 258
    assert counts[NEEDS_PAGE] == 174
    assert counts[ORAL_PRIMARY] == 84
    assert sum(r["learning_focus"].endswith("_JAWI") for r in rows) == 73
    assert len({r["id"] for r in rows}) == 258
    assert all(r["book_printed_page"] is None and r["teacher_sentence"] is None for r in rows)
    return {
        "subject": "Pendidikan Islam", "years": [2, 3],
        "screened_active_lessons": 258,
        "historic_broad_workbook_review_candidates": 191,
        "refined_page_review_candidates": counts[NEEDS_PAGE],
        "oral_and_tasmi_no_forced_book": counts[ORAL_PRIMARY],
        "jawi_priority": 73,
        "by_year": year_counts,
        "by_focus": dict(focus),
        "confirmed_exercise_pages": 0,
        "approved_teacher_sentences": 0,
        "release": "NO_GO",
        "rows": rows,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    d = match_queue()
    Path(args.output).write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in d.items() if k != "rows"}, ensure_ascii=False, indent=2))
