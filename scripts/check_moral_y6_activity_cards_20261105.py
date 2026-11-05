#!/usr/bin/env python3
"""Regression safety: Year6 cards revised to correct textbook without rewriting DSKP SP."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"rpt_2027/pendidikan_moral/year6_crosswalk_DSKP.json").read_text(encoding="utf-8"))
rev=json.loads((ROOT/"audits/pendidikan_moral_y6_kssr2017_edition_migration_20261105.json").read_text(encoding="utf-8"))["revised_edition"]
assert len(data["units"])==len(rev["units"])==14
for unit in (4,7,14):
    p=ROOT/f"materials/pendidikan_moral/year6/unit_{unit:02d}_kad_aktiviti.md"
    s=p.read_text(encoding="utf-8")
    assert "DRAF_SEMAK" in s
    assert "https://fliphtml5.com/sbinx/haph/" in s
    assert data["units"][unit-1]["title"] in s or (unit==14 and data["units"][unit-1]["title"] in s)
    for item in data["units"][unit-1]["sp"]:
        assert item["code"] in s and item["text"] in s, (unit,item)
    for label in ("Kad situasi","Pilihan A","Pilihan B","PdP 1","PdP 2","PdP 3","Checklist PBD","Sumber"):
        assert label in s, (unit,label)
    assert rev["units"][unit-1]["title"] in s, (unit,"wrong 2021 book title")
    if unit==4:
        for term in ("boria","Stadthuys","wau","flora","fauna","m/s 32–33"):
            assert term.casefold() in s.casefold(),(unit,term)
        assert "tidak menghargai pertolongan orang lain" not in s
    if unit==7:
        for term in ("Jalur Gemilang","Hari Kebangsaan","sajak","Malaysia Negaraku Tercinta"):
            assert term in s,(unit,term)
        assert "mengejek orang yang sedang bersedih" not in s
    if unit==14:
        assert "tajuk SK dalam DSKP" in s
        assert "m/s 132" in s
print("PASS 3 Year6 Moral cards: 2021 textbook examples align with DSKP without invented SP text")
print("NOT FINAL READY: activity pages for every SP, teacher PBD and real Telegram delivery remain separate gates")
