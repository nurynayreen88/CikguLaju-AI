#!/usr/bin/env python3
"""RBT staging source integrity and release denial. Stdlib only.

This validates structures and source-linked draft state; it NEVER asserts pedagogical
or textbook visual approval, Word/PDF rendering, or Telegram/Web parity.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    4: {"sp": 57, "hours": [3, 7, 4, 5, 5, 8], "module_count": 6},
    5: {"sp": 34, "hours": [6, 6, 12, 8], "module_count": 4},
    6: {"sp": 23, "hours": [10, 10, 12], "module_count": 3},
}
REQUIRED_STEPS = ("set_induksi", "aktiviti_1", "aktiviti_2",
                  "pengukuhan_penilaian", "penutup")


def check():
    total = 0
    pages_mapped_year4 = 0
    unique_all = set()
    for year, expected in EXPECTED.items():
        source = ROOT / f"rph_standalone/rbt/tahun_{year}/RPH_RBT_T{year}_2027_DRAF.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        lessons = data["pelajaran"]
        assert data["bukan_modul_pengguna"] is True
        assert data["status"] == "DRAF_STAGING"
        assert len(lessons) == 32
        assert len(data["modul"]) == expected["module_count"]
        assert [m["jam_dskp"] for m in data["modul"]] == expected["hours"]
        assert sum(m["jam_dskp"] for m in data["modul"]) == 32
        assert [lesson["pdp"] for lesson in lessons] == list(range(1, 33))
        assert len({lesson["id"] for lesson in lessons}) == 32

        all_sp = {code for l in lessons for code in l["sp_codes"]}
        assert len(all_sp) == expected["sp"], (year, len(all_sp))
        unique_all.update((year, code) for code in all_sp)

        source_page_refs={ref["sp"] for l in lessons for ref in l["rujukan_buku_teks"].get("calon_muka_surat_mengikut_sp", [])}
        if year in (5,6):
            assert source_page_refs == all_sp, (year,len(source_page_refs),len(all_sp))
        for lesson in lessons:
            assert lesson["review"]["release_ready"] is False, lesson["id"]
            assert lesson["review"]["pedagogi_disahkan_individu"] is False
            assert lesson["review"]["halaman_buku_disahkan"] is False
            assert lesson["review"]["telegram_web_native_diuji"] is False
            assert lesson["review"]["status"].startswith("DRAF")
            assert lesson["rujukan_buku_teks"]["muka_surat"] is None
            assert lesson["status_cadangan_projek"] == (
                "CADANGAN_PDP_CIKGULAJU_BUKAN_AKTIVITI_BUKU_DISAHKAN")
            assert len(lesson["sp_fokus_ringkas"]) == len(lesson["sp_codes"])
            assert lesson["artefak_khusus"] and lesson["rubrik_pbd_khusus"]
            assert list(lesson["langkah"]) == list(REQUIRED_STEPS)
            assert sum(step["minit"] for step in lesson["langkah"].values()) == 60
            assert all(lesson["langkah"][step]["aktiviti"] for step in REQUIRED_STEPS)
            for sp in lesson["sp_codes"]:
                assert sp.split(".")[:2] in [sk.split(".") for sk in lesson["sk"]], sp
                assert any(sp in lesson["langkah"][k]["aktiviti"] for k in
                           ("aktiviti_1", "aktiviti_2")), (lesson["id"], sp)
            if year == 4:
                assert lesson["rujukan_buku_teks"]["status"] == (
                    "RUJUKAN_TEKS_DIGITAL_DITEMUI_BELUM_VISUAL_SAH")
                assert lesson["rujukan_buku_teks"]["calon_muka_surat_teks_digital"]
                pages_mapped_year4 += 1
            else:
                assert lesson["rujukan_buku_teks"]["status"] == "BELUM_SAH_HALAMAN"

        rpt = ROOT / f"rpt_2027/rbt/RPT_RBT_T{year}_2027_DRAF.csv"
        with rpt.open(encoding="utf-8-sig", newline="") as f:
            records = list(csv.DictReader(f))
        assert len(records) == 32
        assert records[0]["ID"] == lessons[0]["id"]
        assert records[-1]["ID"] == lessons[-1]["id"]
        assert all(rec["Status"] == "DRAF" for rec in records)
        total += len(lessons)
        print(f"PASS Y{year}: {len(lessons)} PdP, {len(all_sp)} SP, "
              f"{sum(expected['hours'])} jam; release=false")

    evidence = ROOT / "audits/rbt_t4_textbook_sp_page_map_20261106.json"
    record = json.loads(evidence.read_text(encoding="utf-8"))
    assert record["mapped_sp_codes"] == 57
    assert len(record["sp_printed_page_index"]) == 57
    assert record["visual_lesson_approvals"] == 0
    assert pages_mapped_year4 == 32
    assert total == 96 and len(unique_all) == 114
    approvals = json.loads((ROOT / "audits/rbt_t4_t6_manual_release_approval_manifest_20261106.json").read_text(encoding="utf-8"))
    assert approvals["item_count"] == 96
    assert approvals["approvals_granted"] == approvals["release_ready_count"] == 0
    assert len(approvals["individual_review"]) == 96
    assert len({a["id"] for a in approvals["individual_review"]}) == 96
    assert all(a["bukti_halaman_teks"] and
               a["buku_teks_hal_bercetak_calon"] for a in approvals["individual_review"])
    for a in approvals["individual_review"]:
        assert a["release_ready"] is False and a["semakan_individu_guru"] is False
        assert a["aktiviti_dalam_buku_diluluskan"] is False
        assert a["docx_pdf_native_a4_disahkan"] is False
        assert a["rt_web_telegram_verified"] is False
        assert len(a["pending"]) >= 6
    print("PASS 96/96 RPH project-specific (technical checks only).")
    print("Buku Teks T4–6: 96/96 PdP have printed-page candidates, "
          "0/96 independently approved visual tasks.")
    print("NOT FINAL READY. No native Word/PDF or production tests conducted.")


if __name__ == "__main__":
    check()
