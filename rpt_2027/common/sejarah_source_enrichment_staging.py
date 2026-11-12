"""Stage Sejarah 2027 source-controlled week and page crosswalk.

Do not invent calendars or exercise verification. The source CSV remains
untouched; selected candidate A/B ranges and original unit-level page notes
are preserved in each rendered record for audit.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "audits/sejarah_y4_y6_primary_textbook_page_evidence_20261106.json"
MASTER = ROOT / "rpt_2027/common/calendar_week_2027_a_b_snapshot_20261107_DRAF.json"
HOLIDAY = ROOT / "rpt_2027/common/sejarah_group_a_2027_03_14_holiday_index_evidence_DRAF.json"

def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _holiday_explains_group_a_first_day(date_iso):
    """Validate exact KPM-index source evidence; never infer a holiday."""
    src = _read(HOLIDAY)
    states = src.get("a_states", [])
    return (
        src.get("status") == "SOURCE_EVIDENCE_DRAF_RELEASE_SIGNOFF_PENDING"
        and src.get("date") == date_iso == "2027-03-14"
        and src.get("school_group") == "A"
        and {s.get("name") for s in states} == {"Kedah", "Kelantan", "Terengganu"}
        and all(s.get("kpm_holiday") == "Hari Raya Puasa"
                and s.get("pdp_status") == "BUKAN PDP - CUTI RASMI BKPP/KPM"
                for s in states)
    )


def _week_candidates(row, master):
    """Allow exact A/B source week dates, or explicitly flagged A one-day start.

    The latter applies solely where B dates match exactly and A ends match,
    and its original start is one calendar day after master start. It does
    not infer a holiday or alter either date.
    """
    candidates = []
    for a_week, a in master["A"].items():
        b = master["B"].get(a_week)
        if b is None:
            continue
        b_exact = ((row["b_start"], row["b_end"]) == (b["start"], b["end"]))
        a_exact = ((row["a_start"], row["a_end"]) == (a["start"], a["end"]))
        if b_exact and a_exact:
            candidates.append((a_week, "EXACT_SOURCE_DATE_PAIR"))
        elif b_exact and row["a_end"] == a["end"]:
            a_start = date.fromisoformat(row["a_start"])
            expected = date.fromisoformat(a["start"])
            if (a_start == expected + timedelta(days=1) and
                    _holiday_explains_group_a_first_day(expected.isoformat())):
                candidates.append((a_week, "GROUP_A_FIRST_DAY_KPM_HOLIDAY_INDEXED"))
    return candidates


def enrich_sejarah_source_week_and_book(year, records):
    if year not in (4, 5, 6) or len(records) != 36:
        raise ValueError("Sejarah source week/textbook crosswalk expects 36 PdP per Year 4–6")
    ledger = _read(EVIDENCE)
    calendar = _read(MASTER)
    if (ledger.get("count") != 108 or
        ledger.get("status") != "108_DIGITAL_TEXT_PAGE_FOCUS_CROSSWALK_COMPLETED_FINAL_REVIEW_PENDING"
        or calendar.get("status") != "DRAF_REFERENCE_NOT_RELEASE_SIGNOFF"):
        raise ValueError("Sejarah textbook/calendar source evidence changed unexpectedly")
    entries = {(record["year"], record["pdp"]): record for record in ledger["records"]}
    if len(entries) != 108 or any(len({x["week"] for x in calendar["weeks"][g] if x.get("week")}) != 44 for g in ("A", "B")):
        raise ValueError("Sejarah evidence or school week master incomplete")
    weeks = {}
    for group in ("A", "B"):
        weeks[group] = {row["week"]: row for row in calendar["weeks"][group]
                        if re.fullmatch(r"M\d{2}", row.get("week") or "")}
    for row in records:
        number = int(row["id"])
        evidence = entries.get((year, number))
        if not evidence or not evidence.get("pages") or not evidence.get("sp"):
            raise ValueError(f"Sejarah {year} PdP {number:03d}: missing textbook page evidence")
        if any(evidence.get(flag) is not False
               for flag in ("ready", "teacher_approved", "exact_exercise_visual_verified")):
            raise ValueError("Cannot silently import an unexpectedly approved textbook record")
        all_sp = {part.strip() for part in row["sp"].split("/")}
        if not set(evidence["sp"]).issubset(all_sp):
            raise ValueError(f"Sejarah {year} PdP {number:03d}: book SP differs from RPT")
        pages = evidence["pages"].strip()
        if not re.fullmatch(r"\d+(?:[–-]\d+)?(?:,\s*\d+(?:[–-]\d+)?)*", pages):
            raise ValueError(f"Sejarah {year} PdP {number:03d}: invalid sourced pages")
        candidates = _week_candidates(row, weeks)
        if len(candidates) != 1:
            raise ValueError(f"Sejarah {year} PdP {number:03d}: zero/ambiguous matching school weeks")
        week, match_type = candidates[0]
        row["source_week"] = row["week"]
        row["week"] = (week + " (cadangan)" if match_type == "EXACT_SOURCE_DATE_PAIR"
                       else week + " (cadangan; cuti A)")
        row["calendar_alignment"] = match_type
        row["textbook_pages"] = pages
        row["textbook_page_evidence"] = "DIGITAL_TEXT_DRAF_NOT_VISUALLY_APPROVED"
        row["textbook_page_source_urls"] = evidence.get("page_urls", [])
        original_note = row["note"]
        row["source_unit_page_note"] = original_note
        match = re.match(r"^Buku teks: julat halaman UNIT [^()\\n]{3,60} "
                         r"\(bukan halaman aktiviti disahkan\)\. ", original_note)
        if match:
            tail = original_note[match.end():]
        elif original_note.startswith("Halaman buku teks PdP belum disahkan. "):
            # Some Sejarah source rows intentionally lack a unit page range,
            # even though the later per-PdP digital crosswalk has source pages.
            tail = original_note[len("Halaman buku teks PdP belum disahkan. "):]
        else:
            raise ValueError(f"Sejarah {year} PdP {number:03d}: source page note unknown")
        row["note"] = (f"Buku teks m/s {pages} (padanan teks digital DRAF; "
                       "gambar/latihan belum disahkan). " + tail)
        if match_type == "GROUP_A_FIRST_DAY_KPM_HOLIDAY_INDEXED":
            row["note"] += (
                " Kalendar: 14/03/2027 cuti tambahan KPM Hari Raya Puasa Kumpulan A; "
                "PdP calon bermula 15/03/2027. Sahkan jadual guru sebelum diterbitkan."
            )
    return records
