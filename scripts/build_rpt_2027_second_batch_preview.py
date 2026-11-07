"""Additional RPT 2027 five-column previews, sourced from existing DRAFT manifests.

STAGING ONLY. Never switches Telegram/Web download paths or promotes a record.
Sejarah: 36 sourced PdP each (Y4-Y6), date ranges are candidate allocations.
PJPK: preserve *separate* PJ/PK PdP numbering within a combined PDF (Y2-Y6).
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from rpt_2027.common.format_2026_layout_preview import build_preview, validate_rows
from rpt_2027.common.standard_text_enrichment import enrich_sejarah, enrich_pjpk
from rpt_2027.common.sejarah_source_enrichment_staging import enrich_sejarah_source_week_and_book

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "staging" / "rpt_2027_seragam_2026" / "pdf"
SUBJECT_ROW_COUNTS = {"PJ": {2: 37, 3: 38, 4: 34, 5: 33, 6: 34},
                      "PK": {2: 35, 3: 32, 4: 32, 5: 32, 6: 32}}
SEJARAH_UNITS = {4: 11, 5: 12, 6: 10}


def sejarah_records(year: int):
    if year not in SEJARAH_UNITS:
        raise ValueError("Sejarah preview only supports Year 4-6")
    path = ROOT / "rpt_2027" / "sejarah" / f"RPT_SEJARAH_TAHUN_{year}_2027_A_B_DRAF.csv"
    with path.open(encoding="utf-8-sig", newline="") as fp:
        source = list(csv.DictReader(fp))
    if len(source) != 36:
        raise ValueError("Sejarah must contain the 36 source-proposed PdP")
    units = {}
    result = []
    for n, src in enumerate(source, 1):
        ident = f"{n:03d}"
        if src.get("PdP") != str(n) or src.get("ID") != f"SEJ-T{year}-PDP-{ident}":
            raise ValueError("Sejarah source PdP identity/order mismatch")
        if src.get("Status") != "DRAF" or src.get("Jenis") not in ("KANDUNGAN", "KAJIAN_KES"):
            raise ValueError("Sejarah source unexpectedly approved or unknown type")
        raw_unit = src.get("Unit Buku Teks", "").strip()
        if not raw_unit or not src.get("Tema") or not src.get("Tajuk"):
            raise ValueError("Sejarah unit/theme/title source incomplete")
        if raw_unit not in units:
            units[raw_unit] = len(units) + 1
        unit_text = f"Unit {units[raw_unit]}: {raw_unit}"
        pages = (src.get("Halaman Mula Unit", "").strip(),
                 src.get("Halaman Akhir Unit", "").strip())
        page_note = ("Buku teks: julat halaman UNIT " + "-".join(pages)
                     + " (bukan halaman aktiviti disahkan). " if all(pages) else
                     "Halaman buku teks PdP belum disahkan. ")
        result.append({
            "id": ident,
            "week": "Agihan cadangan",  # Dates are candidates, not official week labels.
            "a_start": src["Kumpulan A minggu mula"],
            "a_end": src["Kumpulan A minggu akhir"],
            "b_start": src["Kumpulan B minggu mula"],
            "b_end": src["Kumpulan B minggu akhir"],
            "unit": unit_text,
            "topic": src["Tema"] + " | " + src["Tajuk"] +
                     (" | KAJIAN KES" if src["Jenis"] == "KAJIAN_KES" else ""),
            "sk": src["SK"],
            "sp": src["SP"],
            "note": page_note + "PBD (draf): " +
                    (src.get("Evidens PBD RPH", "").strip() or "Belum disahkan") +
                    ". Tarikh A/B ialah cadangan; semak negeri, cuti dan jadual guru."
        })
    if len(units) != SEJARAH_UNITS[year]:
        raise ValueError("Sejarah sequence does not match sourced book-unit inventory")
    enrich_sejarah(year,result)
    enrich_sejarah_source_week_and_book(year,result)
    validate_rows("sejarah", year, result)
    return result


def _group_range(raw: str):
    """Convert literal DD/MM–DD/MM 2027 source guidance; never manufacture dates."""
    if not isinstance(raw, str):
        raise ValueError("Missing PJPK source date")
    match = re.fullmatch(r"(\d{2})/(\d{2})\s*[–-]\s*(\d{2})/(\d{2})", raw.strip())
    if not match:
        raise ValueError("Invalid PJPK group-week range")
    d1, m1, d2, m2 = map(int, match.groups())
    start = datetime(2027, m1, d1).date()
    end = datetime(2027, m2, d2).date()
    if start > end:
        raise ValueError("PJPK dates reversed or rollover not explicitly sourced")
    return start.isoformat(), end.isoformat()


def _pj_unit_and_title(row):
    title = row["title"].strip()
    match = re.fullmatch(r"UNIT\s+(\d+)\s*[:：]\s*(.*?)\s+TAJUK\s*[:：]\s*(.+)",
                         title, flags=re.IGNORECASE)
    if match:
        return "Unit " + match.group(1) + ": " + match.group(2), match.group(3)
    if row["subject"] == "PK":
        return ("Pendidikan Kesihatan" + (" — " + row["component"]
                if row.get("component") else "")), title
    return "Pendidikan Jasmani", title


def pjpk_records(year: int):
    if year not in range(2, 7):
        raise ValueError("PJPK preview only supports Year 2-6")
    path = ROOT / "rpt_2027/pjpk/pjpk_2027_rpt_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("year") != 2027 or manifest.get("ready") is not False or not (
        str(manifest.get("status", "")).startswith("DRAF")
    ):
        raise ValueError("PJPK manifest is not an unapproved 2027 source")
    weeks = {}
    for item in manifest["weeks"]:
        n = item["week"]
        if not isinstance(n, int) or n in weeks:
            raise ValueError("PJPK duplicated/invalid source week")
        weeks[n] = (_group_range(item["groupA"]), _group_range(item["groupB"]))
    source = [r for r in manifest["records"] if r.get("year") == year]
    by_subject = defaultdict(list)
    for src in source:
        sub = src.get("subject")
        if sub not in ("PJ", "PK") or src.get("ready") is not False or not (
            str(src.get("status", "")).startswith("DRAF")
        ):
            raise ValueError("PJPK unexpected source subject/approval")
        by_subject[sub].append(src)
    for sub, counts in SUBJECT_ROW_COUNTS.items():
        if len(by_subject[sub]) != counts[year]:
            raise ValueError(f"PJPK {sub} Year {year} source count mismatch")
        if sorted(x["pdp"] for x in by_subject[sub]) != list(range(1, counts[year] + 1)):
            raise ValueError(f"PJPK {sub} Year {year} PdP IDs missing/duplicate")
    source.sort(key=lambda x: (x["week"], 0 if x["subject"] == "PJ" else 1, x["pdp"]))
    result = []
    for n, src in enumerate(source, 1):
        week = src["week"]
        if week not in weeks or not src.get("title") or not src.get("sk") or not src.get("sp"):
            raise ValueError("PJPK record has unknown week or missing SK/SP/topic")
        (a_start, a_end), (b_start, b_end) = weeks[week]
        unit, topic = _pj_unit_and_title(src)
        book = str(src.get("bt") or "").strip()
        book_note = ("Rujukan: " + book + ". " if book.lower().startswith("rujuk") else
                     "Buku teks m/s " + book + ". " if book else "")
        note = ("Sumber: " + src.get("origin", "DRAF") + ". " + book_note +
                ("Masa: " + str(src["duration_min"]) + " minit. "
                 if src.get("duration_min") else ""))
        if src.get("activity_source"):
            note += "Aktiviti (sumber): " + src["activity_source"].strip() + ". "
        if src.get("assessment_source"):
            note += "PBD (sumber): " + src["assessment_source"].strip() + ". "
        note += "DRAF: minggu/tarikh calon; sahkan jadual dan cuti negeri."
        result.append({
            "id": f"{n:03d}",  # table display order only; not the original source ID
            "display_id": f"{src['subject']} PdP {src['pdp']:03d}",
            "week": f"M{week:02d} (cadangan)",
            "a_start": a_start, "a_end": a_end,
            "b_start": b_start, "b_end": b_end,
            "unit": unit, "topic": topic,
            "sk": ", ".join(str(v) for v in src["sk"]),
            "sp": ", ".join(str(v) for v in src["sp"]),
            "note": note
        })
    enrich_pjpk(year,result)
    validate_rows("pjpk", year, result)
    return result


def build_all(destination=OUTPUT):
    destination = Path(destination)
    built = []
    for subject, years, loader in (
        ("sejarah", range(4, 7), sejarah_records),
        ("pjpk", range(2, 7), pjpk_records),
    ):
        for year in years:
            records = loader(year)
            if any(not row.get("sk_display") or not row.get("sp_display") for row in records):
                raise ValueError("All staged RPT rows must have full sourced SK/SP statements")
            path = destination / (
                f"CIKGULAJU_RPT_{subject.upper()}_TAHUN_{year}_2027_FORMAT_SERAGAM_DRAF.pdf")
            build_preview(subject, year, records, path)
            built.append((subject, year, len(records), path))
    return built


if __name__ == "__main__":
    for subject, year, count, file in build_all():
        print(f"{subject.upper()} Tahun {year}: {count} PdP -> {file}")
