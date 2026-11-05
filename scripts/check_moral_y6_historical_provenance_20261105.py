#!/usr/bin/env python3
"""Ensure Year6 Moral RPH do not pass off old textbook evidence as revised 2021 edition."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDITS=ROOT/"audits"
RPT=ROOT/"rpt_2027/pendidikan_moral"

def main():
    history=json.loads((AUDITS/"pendidikan_moral_y6_visual24_units05_13_20261105.json").read_text(encoding="utf-8"))
    migration=json.loads((AUDITS/"pendidikan_moral_y6_kssr2017_edition_migration_20261105.json").read_text(encoding="utf-8"))
    units=migration["revised_edition"]["units"]
    historical={r["lesson"]:r for r in history["records"]}
    assert len(historical)==24
    assert "HISTORICAL_OLD_EDITION" in history["status"]
    assert "DO NOT verify" in history["method"]
    examined=0
    revised_text=0
    chapter_only=0
    for n in range(1,43):
        unit=(n-1)//3+1
        path=ROOT/f"rph_standalone/pendidikan_moral/year6/lesson_{n:03d}.md"
        source=path.read_text(encoding="utf-8")
        assert "DRAF SEMAK" in source and "BELUM READY" in source,path
        assert "https://fliphtml5.com/sbinx/haph/" in source,path
        assert units[unit-1]["title"].casefold() in source.casefold(), (n,unit,"missing revised-edition unit title")
        assert "**Bukti buku teks disemak (2026-11-05):**" not in source,path
        if n in historical:
            r=historical[n]
            old=f"m/s {r['printed'][0]}–{r['printed'][1]} (PDF {r['pdf'][0]}–{r['pdf'][1]})"
            assert "Rekod audit sejarah — buku edisi lama, bukan bukti Semakan 2017" in source,path
            assert old in source and "bukti aktiviti buku teks DBP 2021" in source,path
        if unit in (4,7):
            assert "Pengesahan sumber Semakan 2017" in source,path
            revised_text+=1
        else:
            assert "Padanan bab edisi Semakan 2017" in source,path
            assert "bukan semakan visual" in source.casefold() or "bukan semakan visual penuh" in source.casefold(),path
            chapter_only+=1
        activities=[p for p in source.splitlines() if p.startswith(("**Aktiviti 1 (20 minit)","**Aktiviti 2 (20 minit)"))]
        assert len(activities)==2 and all("Guru" in a and "Murid" in a for a in activities),path
        examined+=1
    assert (examined,revised_text,chapter_only)==(42,6,36)
    print("PASS 42 Year6 Moral core RPH: 24 old scanned-edition references clearly HISTORICAL, 6 text-checked current-book, 36 chapter-linked only")
    print("NOT FINAL READY: 36 current-edition individual activity pages still need verification; no real Telegram teacher account proof")

if __name__=="__main__":
    main()
