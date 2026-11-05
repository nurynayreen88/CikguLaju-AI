#!/usr/bin/env python3
"""Individual, read-only evidence ledger for 480 Pendidikan Moral RPH sessions.

This produces a per-RPH CSV; it does not claim visual approval of scanned
textbook activity pages or write databases/release flags. Original DSKP SP
source texts are certified separately by check_moral_official_dskp_350sp.py.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RPT = ROOT / "rpt_2027/pendidikan_moral"
AUDITS = ROOT / "audits"
PHASES = ("Set induksi", "Aktiviti 1", "Aktiviti 2",
          "Pengukuhan/Pentaksiran PBD", "Penutup")
FIELDS = ("Tahun", "Sesi", "Modul", "Unit", "SK", "SP",
          "RPH", "Source_SHA256_16", "DSKP_Text_And_Structure",
          "Buku_Unit_Heading", "Buku_Aktiviti_SP", "Keputusan_Terus",
          "Audit_Pedagogi_Manual", "Word_A4_Dirender",
          "Telegram_Akaun_Sebenar")


def book_verified_pairs() -> set[tuple[int, int]]:
    a = json.loads((AUDITS / "pendidikan_moral_y2_y6_units02_03_visual_30pdp_20261104.json").read_text(encoding="utf-8"))
    b = json.loads((AUDITS / "pendidikan_moral_unit4_y2_y5_12_visual_20261104.json").read_text(encoding="utf-8"))
    checked: set[tuple[int, int]] = set()
    for u in a["records"]:
        for phase in u["phases"]:
            n = (u["unit"] - 1) * 3 + phase["phase"]
            assert (u["year"], n) not in checked, (u["year"], n)
            checked.add((u["year"], n))
    assert len(checked) == 33
    for r in b["entries"]:
        pair = (r["year"], r["lesson"])
        assert pair not in checked, pair
        checked.add(pair)
    assert len(checked) == 45, len(checked)
    third = json.loads((AUDITS / "pendidikan_moral_visual21_unit1_unit5_20261105.json").read_text(encoding="utf-8"))
    new_pairs = {(r["year"], r["lesson"]) for r in third["records"]}
    assert len(new_pairs) == len(third["records"]) == 21
    assert not (checked & new_pairs), "newly verified book RPH overlap prior evidence"
    checked.update(new_pairs)
    assert len(checked) == 66, len(checked)
    y2 = json.loads((AUDITS / "pendidikan_moral_visual27_y2_u06_u14_20261105.json").read_text(encoding="utf-8"))
    y2_pairs = {(r["year"], r["lesson"]) for r in y2["records"]}
    assert len(y2_pairs) == 27 and not (checked & y2_pairs), "Year2 extra source review overlap"
    checked.update(y2_pairs)
    assert len(checked) == 93, len(checked)
    y3 = json.loads((AUDITS / "pendidikan_moral_visual27_y3_u06_u14_20261105.json").read_text(encoding="utf-8"))
    y3_pairs = {(r["year"], r["lesson"]) for r in y3["records"]}
    assert len(y3_pairs) == 27 and not (checked & y3_pairs), "Year3 source review duplicates"
    checked.update(y3_pairs)
    assert len(checked) == 120, len(checked)
    y4 = json.loads((AUDITS / "pendidikan_moral_visual30_y4_u05_u14_20261105.json").read_text(encoding="utf-8"))
    y4_pairs = {(r["year"], r["lesson"]) for r in y4["records"]}
    assert len(y4_pairs) == 30 and not (checked & y4_pairs), "Year4 duplicated audit entries"
    checked.update(y4_pairs)
    assert len(checked) == 150, len(checked)
    y5 = json.loads((AUDITS / "pendidikan_moral_visual30_y5_u05_u14_20261105.json").read_text(encoding="utf-8"))
    y5_pairs = {(r["year"], r["lesson"]) for r in y5["records"]}
    assert len(y5_pairs) == 30 and not (checked & y5_pairs), "Year5 source review overlaps previous evidence"
    checked.update(y5_pairs)
    assert len(checked) == 180, len(checked)
    y6 = json.loads((AUDITS / "pendidikan_moral_y6_visual24_units05_13_20261105.json").read_text(encoding="utf-8"))
    y6_pairs = {(r["year"], r["lesson"]) for r in y6["records"]}
    assert len(y6_pairs) == 24 and not (checked & y6_pairs), "Year6 24 source evidence records duplicated"
    checked.update(y6_pairs)
    assert len(checked) == 204, len(checked)
    return checked, new_pairs | y2_pairs | y3_pairs | y4_pairs | y5_pairs | y6_pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Destination CSV; never overwrites source RPH/RPT")
    args = parser.parse_args()
    dest = Path(args.output).resolve()
    assert ROOT not in dest.parents, "Audit output must stay outside version-controlled repository"

    # This test uses original KPM DSKP PDF-derived source fingerprints. Any
    # changed SP source text fails before the 480 lesson checks begin.
    from check_moral_official_dskp_350sp import run as verify_dskp
    verify_dskp()

    visual, new_visual = book_verified_pairs()
    output = []
    counts = Counter()
    matched = set()
    for year in range(2, 7):
        cross = json.loads((RPT / f"year{year}_crosswalk_DSKP.json").read_text(encoding="utf-8"))
        toc = json.loads((RPT / f"year{year}_book_toc_VERIFIED.json").read_text(encoding="utf-8"))
        with (RPT / f"year{year}_96h_coverage_PLANNING.csv").open(encoding="utf-8", newline="") as f:
            sessions = list(csv.DictReader(f))
        assert len(sessions) == 96
        for r in sessions:
            n = int(r["Sesi_1_96"])
            assert 1 <= n <= 96
            unit_id = int(r["Unit"])
            u = cross["units"][unit_id - 1]
            assert u["unit"] == unit_id and r["SK"] == u["sk"]
            assert r["SP"].split("; ") == [e["code"] for e in u["sp"] if e["code"] in r["SP"].split("; ")]
            src_path = ROOT / r["Rujukan_RPH_Sedia_Ada"]
            assert src_path.is_file(), (year, n, src_path)
            source = src_path.read_text(encoding="utf-8")
            assert len(source) >= (1800 if r["Modul"] == "TERAS" else 2000)
            assert all(f"**{phase}" in source for phase in PHASES), (year, n, "phase")
            assert "Objektif dan kriteria kejayaan" in source and "60 minit" in source
            assert "PBD" in source and "Guru" in source and "Murid" in source
            for code in r["SP"].split("; "):
                original_text = next(x["text"] for x in u["sp"] if x["code"] == code)
                assert original_text in source and code in source, (year, n, code)
            assert r["Modul"] in ("TERAS", "PENGUKUHAN")
            if r["Modul"] == "TERAS":
                lesson = int(r["PdP_Teras_Asal"])
                assert f"PdP {lesson:03d}" in source
                key = (year, lesson)
                book_activity = ("VISUAL_REKOD_SP_20261105" if key in new_visual else "VISUAL_REKOD_SP_20261104") if key in visual else "BELUM_DISAHKAN_HALAMAN_AKTIVITI"
                counts["core"] += 1
                if key in visual:
                    counts["core_book_visual_historical"] += 1
                if year < 6:
                    if key in visual:
                        counts["core_correct_edition_y2_y5"] += 1
                elif lesson in (10, 11, 12, 19, 20, 21):
                    assert "Pengesahan sumber Semakan 2017" in source
                    book_activity = "SEMAKAN2017_TEKSTUAL_TERAS_BUKAN_PDF_LEGASI"
                    counts["core_y6_revised_source_text"] += 1
                elif key in visual:
                    assert "Padanan bab edisi Semakan 2017" in source
                    book_activity = "SEMAKAN2017_PADANAN_TAJUK_BAB_SP_TANPA_SEMAK_VISUAL_TUGAS"
                    counts["core_y6_revised_topic_only"] += 1
                else:
                    raise AssertionError((year, lesson, "unsighted Year6 core RPH in historical ledger"))
                    book_activity = "TAHUN6_EDISI_SEMAKAN2017_BELUM_DISAHKAN"
                    counts["core_y6_not_previously_reviewed"] += 1
            else:
                assert f"Sesi {n:03d}" in source
                book_activity = "BELUM_DISAHKAN_HALAMAN_AKTIVITI"
                counts["supplement"] += 1
                if year < 6:
                    counts["supp_y2_y5_not_individually_book_verified"] += 1
                elif n in (24, 25, 26, 27, 45, 46, 47, 48):
                    assert "Bukti aktiviti Semakan 2017" in source
                    book_activity = "SEMAKAN2017_TEKSTUAL_PENGUKUHAN_BUKAN_PDF_LEGASI"
                    counts["supp_y6_revised_source_text"] += 1
                else:
                    book_activity = "EDISI_SEMAKAN2017_Y6_AKTIVITI_BELUM_DISAHKAN"
                    counts["supp_y6_old_edition_recheck"] += 1
            held = year == 6 and unit_id in (4, 7)
            stage = r["Tahap_Semakan_Buku"]
            if held:
                assert stage == f"HOLD_SOURCE_MISMATCH_UNIT{unit_id}_Y6"
                if "SEMAKAN2017_TEKSTUAL_" in book_activity:
                    book_activity += "_RPT_HOLD_SEHINGGA_SEMUA_SUMBER_DIKEMASKINI"
                else:
                    book_activity = "HOLD_PERCANGGAHAN_DSKP_BUKU"
                counts["source_hold"] += 1
            else:
                assert stage == "VERIFIED_TOC_START_ONLY"
            assert toc["units"][unit_id - 1]["heading_verification_scope"] == "BOOK_OPENING_PAGE_VISUAL_ONLY"
            assert (year, n) not in matched, (year, n)
            matched.add((year, n))
            output.append({
                "Tahun": year, "Sesi": f"{n:03d}", "Modul": r["Modul"], "Unit": unit_id,
                "SK": r["SK"], "SP": r["SP"], "RPH": r["Rujukan_RPH_Sedia_Ada"],
                "Source_SHA256_16": hashlib.sha256(source.encode("utf-8")).hexdigest()[:16],
                "DSKP_Text_And_Structure": "DISAHKAN_AUTOMATIK",
                "Buku_Unit_Heading": "VISUAL_DISAHKAN_UNIT_MULA_SAHAJA",
                "Buku_Aktiviti_SP": book_activity,
                "Keputusan_Terus": "TIDAK_FINAL_READY_TUNGGU_AUDIT_BUKU_DAN_TELEGRAM",
                "Audit_Pedagogi_Manual": "BELUM_DISEDIAKAN_BUKTI_SELURUH_RPH",
                "Word_A4_Dirender": "BELUM_UJI_SEMUA_RPH_WORD_A4",
                "Telegram_Akaun_Sebenar": "BELUM_UJI_HANTAR_KE_AKAUN_GURU",
            })
    assert len(output) == len(matched) == 480, (len(output), len(matched))
    assert counts == {
        "core": 210, "core_book_visual_historical": 204,
        "core_correct_edition_y2_y5": 168,
        "core_y6_revised_source_text": 6,
        "core_y6_revised_topic_only": 36,
        "supplement": 270,
        "supp_y2_y5_not_individually_book_verified": 216,
        "supp_y6_revised_source_text": 8,
        "supp_y6_old_edition_recheck": 46,
        "source_hold": 14,
    }, counts
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    assert dest.stat().st_size > 40000, dest.stat().st_size
    print(f"PASS INDIVIDUAL EVIDENCE LEDGER: 480/480 records, {dict(counts)}")
    print(f"Saved: {dest}")
    print("NOT FINAL READY: 204 historical visual checks included 36 Year6 references to OBSOLETE textbook edition.")
    print("Correct-edition core: 168 Y2-Y5 visual + 6 Y6 revised source-text tasks = 174 with activity-linked evidence.")
    print("The remaining 36 Year6 core now have revised-edition chapter/SP mappings ONLY (not detailed textbook activity review).")
    print("270 supplementary: 8 Year6 revised-book references mapped, 262 still lack individual current-book verification.")
    print("14 Year6 unit 4/7 sessions remain RPT historical HOLD pending complete edition migration and true teacher delivery.")
    print("Word A4 all-session visual and actual Telegram account delivery are separate release gates.")


if __name__ == "__main__":
    main()
