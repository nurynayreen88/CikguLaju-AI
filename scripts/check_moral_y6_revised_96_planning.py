#!/usr/bin/env python3
"""Safety gate: Year6 revised-edition 96 RPH/RPT preview, never READY or DB-mutating."""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"rpt_2027/pendidikan_moral"
AUD=ROOT/"audits/pendidikan_moral_y6_kssr2017_edition_migration_20261105.json"

def main():
    mig=json.loads(AUD.read_text(encoding="utf-8"))
    revised=mig["revised_edition"]
    units=revised["units"]
    assert len(units)==14 and [x["unit"] for x in units]==list(range(1,15))
    with (BASE/"year6_96h_coverage_SEMAKAN2017_REVIEW.csv").open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    with (BASE/"year6_96h_coverage_PLANNING.csv").open(encoding="utf-8",newline="") as f:
        original=list(csv.DictReader(f))
    assert len(rows)==len(original)==96
    assert [r["Sesi_1_96"] for r in rows]==[f"{i:03d}" for i in range(1,97)]
    core=supp=reviewed=0
    for row,old in zip(rows,original):
        n=int(row["Sesi_1_96"]); unit=int(row["Unit"]); mod=row["Modul"]
        entry=units[unit-1]; hold=unit in (4,7)
        assert row["Rujukan_Edisi"]=="KSSR_SEMAKAN_2017_DBP_2021_PUBLIC_FLIPBOOK"
        assert int(row["Halaman_Mula_Unit_Buku"])==entry["printed_start"]
        assert int(row["Mula_Halaman_Flipbook"])==entry["printed_start"]+10
        assert row["Tajuk_Unit"]==entry["title"], (n, row["Tajuk_Unit"], entry["title"])
        assert row["Tahap_Semakan_Buku"]==("SEMAKAN2017_TEKSTUAL_SP_KEGIATAN_DIKAITKAN" if hold else "SEMAKAN2017_BAB_SP_SAHAJA_BELUM_AUDIT_AKTIVITI")
        assert row["Bukti_Individu"]=="BELUM_FINAL_READY"
        assert "semakan 2017" in row["Nota_Sumber"].casefold()
        assert not ("READY" in row["Status_Dalaman"] and "BETA" not in row["Status_Dalaman"])
        # Only source metadata may differ; original RPH/SC/SP/session order retained.
        for field in original[0]:
            if field not in ("Halaman_Mula_Unit_Buku","Tahap_Semakan_Buku","Tajuk_Unit"):
                assert row[field]==old[field], (n, field)
        path=ROOT/row["Rujukan_RPH_Sedia_Ada"]
        assert path.is_file(), (n,path)
        source=path.read_text(encoding="utf-8")
        for code in row["SP"].split("; "):
            assert code in source, (n,code)
        if mod=="TERAS":core+=1
        elif mod=="PENGUKUHAN":supp+=1
        else:raise AssertionError(mod)
        if hold:reviewed+=1
    assert (core,supp,reviewed)==(42,54,14)

    # The two teacher-facing printable RPT sources must use identical revised-edition
    # unit titles; no changes to week blocks, class dates, SP or lesson order.
    for group in ("A","B"):
        with (BASE/f"year6_sequence_96_2027_group{group}_STAGING.csv").open(encoding="utf-8",newline="") as f:
            printable=list(csv.DictReader(f))
        assert len(printable)==96
        assert [r["Sesi"] for r in printable]==[f"{i:03d}" for i in range(1,97)]
        for i,(printed,canonical) in enumerate(zip(printable,rows),start=1):
            assert printed["Kumpulan"]==group
            assert printed["Unit"]==canonical["Unit"]
            assert printed["Tajuk_Unit"]==canonical["Tajuk_Unit"], (group,i,"obsolete textbook title")
            assert printed["SP"]==canonical["SP"]
            assert printed["Rujukan_RPH"]==canonical["Rujukan_RPH_Sedia_Ada"]
            assert printed["Status_Dalaman"]==("RPH_TERSEDIA_BETA80" if printed["Modul"]=="TERAS" else "RPH_PENGUKUHAN_DRAF_SUMBER_TOC")

    print("PASS: Year6 96 sessions crosswalk 2021 textbook edition, 42 core + 54 supplement, 14 source-textual unit4/7")
    print("UNRESOLVED: 82 chapter-only activity-level verifications; teacher dates, user-facing Word A4 and Telegram real delivery remain separate gates")

if __name__=="__main__":
    main()
