#!/usr/bin/env python3
"""Read-only staging structural QA: 60 Bahasa Arab PdP drafts, 20 units, 15 banks.
NOT a pedagogical approval, RPT 2027 release, source page certification or production patch.
"""
from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = ROOT / "rph_standalone" / "bahasa_arab"
RPT = ROOT / "rpt_2027" / "bahasa_arab"
EXPECTED_SP = {2:["1.1.1","1.1.2","1.2.1","2.1.1","2.2.1","3.1.1","3.2.1","1.3.1","1.3.2","2.3.1","3.3.1","1.4.1"],3:["1.1.1","1.1.2","1.2.1","2.1.1","2.2.1","3.1.1","3.2.1","1.3.1","1.3.2","2.3.5","3.3.1","1.4.1"],4:["1.1.1","1.1.2","1.2.1","2.1.1","2.2.1","3.1.1","3.2.1","1.3.1","1.3.2","2.3.1","3.3.1","1.4.1"],5:["1.1.1","1.1.2","1.2.1","2.1.1","2.2.1","3.2.1","1.3.1","1.3.2","2.3.1","2.3.2","3.3.1","1.4.1"],6:["1.1.1","1.1.2","1.2.1","2.1.2","2.2.1","3.1.1","1.3.1","1.3.2","2.3.1","2.3.2","3.2.1","1.4.1"]}
UNIT_1 = {2:"هيا نتعارف",3:"تفضل إلى الفصل",4:"الشهور الميلادية",5:"في المطبخ",6:"حياتنا أجمل بالنظافة"}
MARKERS = ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Penutup", "BBM",
           "PBD", "Kriteria kejayaan", "Refleksi", "DRAF", "BELUM READY")
def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def check() -> None:
    m = json.loads((SUBJECT / "source_manifest_20261105.json").read_text(encoding="utf-8"))
    assert m["release_status"] == "DRAF_STAGING_SAHAJA"
    assert m["total_final_ready_rph"] == 0
    assert all(m[key] is False for key in ("production_db_touched", "telegram_live_touched", "web_live_touched"))
    assert sorted(m["years"]) == ["2","3","4","5","6"]
    units = read_csv(RPT / "unit_sequence_DRAF_20261105.csv")
    assert len(units) == 20
    assert Counter(int(row["tahun"]) for row in units) == Counter({y:4 for y in range(2,7)})
    assert all(row["status"] == "DRAF_SEMAK" and row["pdp_ready"] == "FALSE" for row in units)
    assert next(x["tajuk_arab"] for x in units if x["tahun"] == "3" and x["unit"] == "4") == "الزمان"
    assert {(int(x["tahun"]),int(x["unit"])) for x in units} == {(y,n) for y in range(2,7) for n in range(1,5)}
    assert m["primary_crosswalk_file"] == "rpt_2027/bahasa_arab/pdp_001_012_DRAF.csv"
    rows = read_csv(RPT / "pdp_001_012_DRAF.csv")
    assert len(rows) == 60
    assert Counter(int(x["tahun"]) for x in rows) == Counter({y:12 for y in range(2,7)})
    assert all(x["status"] == "DRAF_SEMAK" and x["ready"] == "FALSE" and x["halaman_buku_disahkan"] == "FALSE" for x in rows)
    mapping = {(int(x["tahun"]),int(x["pdp"])):x for x in rows}
    assert len(mapping) == 60
    for y in range(2,7):
        s = m["years"][str(y)]
        assert s["provisional_rph_count"] == 12
        assert s["textbook"]["source_page_verified"] is False
        for n in range(1,13):
            p = SUBJECT / f"year{y}" / f"lesson_{n:03d}.md"
            text = p.read_text(encoding="utf-8")
            row = mapping[(y,n)]
            assert row["unit"] == "1"
            assert row["sp"] == EXPECTED_SP[y][n-1]
            assert all(marker in text for marker in MARKERS), p
            assert f"PdP {n:03d}" in text and f"Bahasa Arab Tahun {y}" in text
            assert row["sp"] in text and UNIT_1[y] in text
            assert s["rpt_2026"] in text
            assert len(text) > 1000, p
    banks = 0
    for y in range(2,7):
        for u in range(2,5):
            p = ROOT / "materials" / "bahasa_arab" / f"year{y}" / f"unit_{u:02d}_activity_bank_DRAF.md"
            text = p.read_text(encoding="utf-8")
            assert f"Bahasa Arab Tahun {y}" in text and "Bukti PBD" in text
            assert all(m in text for m in ("DRAF_SEMAK", "BELUM READY", "https://anyflip.com/"))
            banks += 1
    assert banks == m["additional_unit_activity_bank_count"] == 15
    y6_evidence = json.loads((ROOT / "audits" / "bahasa_arab_y6_textbook_page_evidence_20261105.json").read_text(encoding="utf-8"))
    assert y6_evidence["year"] == 6 and y6_evidence["individual_rph_approval"] is False
    assert y6_evidence["all_unit_pages_verified_at_toc_level"] is True
    assert len(y6_evidence["book"]["toc"]) == 4
    assert [(u["printed_page_start"], u["printed_page_end"]) for u in y6_evidence["book"]["toc"]] == [(1,30),(31,60),(61,90),(91,120)]
    assert m["years"]["6"]["textbook"]["source_page_verified"] is False
    assert all(x["ready"] is False for x in y6_evidence["lesson_candidates"])
    assert len(y6_evidence["lesson_candidates"]) == 12
    assert len(y6_evidence["conflicts"]) >= 1
    for idx, row in enumerate(y6_evidence["book"]["toc"], start=1):
        found = next(r for r in units if r["tahun"]=="6" and r["unit"]==str(idx))
        assert found["halaman_mula_buku"] == str(row["printed_page_start"])
        assert found["halaman_akhir_buku"] == str(row["printed_page_end"])
        assert found["status"] == "DRAF_SEMAK" and found["pdp_ready"] == "FALSE"
    print("PASSED: 20 unit indexes, 60 crosswalks, 60 RPH draft files, 15 banks.")
    print("RELEASE BLOCKED: 0 READY; page-level textbook, A4 RTL and manual review missing.")

if __name__ == "__main__":
    check()
