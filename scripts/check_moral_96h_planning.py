#!/usr/bin/env python3
"""Read-only 480-session DSKP/RPH integrity + 44-week A/B schedule checks.

The gate verifies usable source coverage and integrity, not exhaustive visual
textbook validation, exact class timetable or full pedagogy approval.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
RPT = ROOT / "rpt_2027" / "pendidikan_moral"
MASTER = RPT / "induk_minggu_2027_ab.json"
REQUIRED_SECTIONS = (
    "Set induksi", "Aktiviti 1", "Aktiviti 2",
    "Pengukuhan/Pentaksiran PBD", "Penutup",
    "Objektif dan kriteria kejayaan",
)
TOTAL = {"core": 0, "extra": 0, "sessions": 0, "rpt_group_rows": 0}


def check_year(y, master):
    mapping = json.loads((RPT / f"year{y}_crosswalk_DSKP.json").read_text(encoding="utf-8"))
    assert mapping["status"] == "DRAF_SEMAK" and len(mapping["units"]) == 14, y
    with (RPT / f"year{y}_96h_coverage_PLANNING.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 96, (y, len(rows))
    assert [r["Sesi_1_96"] for r in rows] == [f"{i:03d}" for i in range(1, 97)], y
    assert all(r["Tahun"] == str(y) for r in rows), y
    assert sum(int(r["Tempoh_Minit"]) for r in rows) == 96 * 60, y
    core = [r for r in rows if r["Modul"] == "TERAS"]
    extra = [r for r in rows if r["Modul"] == "PENGUKUHAN"]
    assert len(core) == 42 and len(extra) == 54, (y, len(core), len(extra))
    assert [r["PdP_Teras_Asal"] for r in core] == [f"{i:03d}" for i in range(1, 43)], y
    for r in rows:
        unit = mapping["units"][int(r["Unit"]) - 1]
        sp_codes = [x["code"] for x in unit["sp"]]
        actual_codes = r["SP"].split("; ")
        assert r["SK"] == unit["sk"] and all(s in sp_codes for s in actual_codes), (y, r)
        assert not r["Tarikh_Kumpulan_A"] and not r["Tarikh_Kumpulan_B"], y
        assert "READY" not in r["Status_Dalaman"], (y, r)
        path = ROOT / r["Rujukan_RPH_Sedia_Ada"]
        assert path.is_file(), (y, r["Rujukan_RPH_Sedia_Ada"])
        source = path.read_text(encoding="utf-8")
        if y == 6 and r["Unit"] == "4":
            # The verified Book TOC has a DIFFERENT Unit 4 topic from DSKP SK4.
            # Keep all seven Year 6 planning sessions on source hold.
            assert r["Tahap_Semakan_Buku"] == "HOLD_SOURCE_MISMATCH_UNIT4_Y6", (y, r["Sesi_1_96"])
            assert "Jasa Tokoh Negara Dikenang" not in r["Aktiviti_Guru"], (y, r["Sesi_1_96"])
            if r["Modul"] == "PENGUKUHAN":
                assert "**BBM:** Kad pameran keunikan budaya" in source, path
                assert "tidak mendakwa rujukan halaman buku teks" in source, path
            else:
                assert "Unit 4 buku teks" in source, path
        else:
            assert r["Tahap_Semakan_Buku"] == "VERIFIED_TOC_START_ONLY", (y, r["Sesi_1_96"])
        if r["Modul"] == "PENGUKUHAN":
            assert r["Status_Dalaman"] == "RPH_PENGUKUHAN_DRAF_SUMBER_TOC", y
            assert f"Sesi {r['Sesi_1_96']}" in source, (y, path)
            assert ("Tempoh" in source or "Masa:" in source or
                    "cadangan 60 minit" in source), path
            assert "60 minit" in source, path
            assert len(source) >= 2000, path
            if y == 6 and r["Unit"] == "4":
                assert "tidak mendakwa rujukan halaman buku teks" in source, path
            else:
                assert "halaman" in source.lower() and "permulaan" in source.lower(), path
            for section in REQUIRED_SECTIONS:
                assert section in source, (y, path, section)
            codes = actual_codes
            expected = [x for x in unit["sp"] if x["code"] in codes]
            assert all(x["text"] in source and x["code"] in source for x in expected), (y, path)
        else:
            assert r["Status_Dalaman"] == "RPH_TERSEDIA_BETA80", y
            assert f"PdP {r['PdP_Teras_Asal']}" in source, path
            assert "60 minit" in source and "Kriteria kejayaan:" in source, path
            assert len(source) >= 1800, path
            for section in REQUIRED_SECTIONS:
                assert section in source, (y, path, section)
            expected = [x for x in unit["sp"] if x["code"] in actual_codes]
            assert len(expected) == len(actual_codes), (y, path, actual_codes)
            assert all(x["text"] in source for x in expected), (y, path, actual_codes)
            assert "PBD" in source and "Guru" in source and "Murid" in source, path
    weeks_a = master["weeks"]["A"]
    weeks_b = master["weeks"]["B"]
    assert len(weeks_a) == 44 and len(weeks_b) == 44
    for group in ("A", "B"):
        weeks = master["weeks"][group]
        path = RPT / f"year{y}_sequence_96_2027_group{group}_STAGING.csv"
        with path.open(encoding="utf-8", newline="") as f:
            rpt = list(csv.DictReader(f))
        assert len(rpt) == 96, (y, group)
        seen_weeks = set()
        previous_week = 0
        for i, (a, b) in enumerate(zip(rows, rpt), 1):
            wk_id = b["Minggu_RPT"]
            wi = int(wk_id[1:])
            assert 1 <= wi <= 44 and wi >= previous_week, (y, group, i, wk_id)
            previous_week = wi
            wk = weeks[wi - 1]
            assert wk["week"] == wk_id
            assert (b["Tarikh_Minggu_Mula"], b["Tarikh_Minggu_Tamat"]) == (wk["start"], wk["end"])
            assert date.fromisoformat(wk["start"]) <= date.fromisoformat(wk["end"])
            assert b["Sesi"] == a["Sesi_1_96"]
            assert b["SP"] == a["SP"] and b["SK"] == a["SK"]
            assert b["Rujukan_RPH"] == a["Rujukan_RPH_Sedia_Ada"]
            assert b["Modul"] == a["Modul"] and b["Status_Dalaman"] == a["Status_Dalaman"]
            assert b["Aktiviti_Guru"] == a["Aktiviti_Guru"], (y, group, i, "RPT activity drift")
            assert not b["Tarikh_Kelas_Guru"], (y, group, i)
            seen_weeks.add(wk_id)
        assert len(seen_weeks) == 44, (y, group, "Missing a teaching week")
        TOTAL["rpt_group_rows"] += len(rpt)
    TOTAL["core"] += len(core)
    TOTAL["extra"] += len(extra)
    TOTAL["sessions"] += len(rows)
    print(f"Year {y}: 96/96 mapped, 42 core + 54 supplemental RPH, Group A/B M01-M44")


def main():
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    assert master["source"]["tab"] == "INDUK MINGGU RPT 2027 A B"
    for y in range(2, 7):
        check_year(y, master)
    assert TOTAL == {"core": 210, "extra": 270, "sessions": 480, "rpt_group_rows": 960}, TOTAL
    print("PASS SOURCE COVERAGE & WEEK MAPPING:", TOTAL)
    print("CAVEAT: exact textbook activities for all RPH, class-date, Word A4, real Telegram delivery still require separate verification")


if __name__ == "__main__":
    main()
