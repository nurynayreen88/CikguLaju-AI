#!/usr/bin/env python3
"""Guard Year6 Unit2 three source-text-linked core RPH without claiming visual sign-off."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/"audits/pendidikan_moral_y6_unit02_pdp004_006_text_review_20261105.json").read_text(encoding="utf-8"))
assert [x["lesson"] for x in audit["lesson_records"]]==[4,5,6]
assert audit["teacher_release_gate"]=="NOT_FINAL_READY"
checks={
4:("MRT","Derma Darah","polis dan RELA","SP 2.1–2.2"),
5:("JKM","Veronica","m/s 18","SP 2.3–2.4"),
6:("Bumi Hijau","AADK/PPDa","m/s 20","SP 2.5"),
}
for n,terms in checks.items():
    s=(ROOT/f"rph_standalone/pendidikan_moral/year6/lesson_{n:03d}.md").read_text(encoding="utf-8")
    assert all(x in s for x in terms),(n,terms)
    assert "DRAF SEMAK" in s and "BELUM READY" in s,n
    assert "Padanan bab edisi Semakan 2017" in s,n
    assert s.count("**Aktiviti 1 (20 minit)")==1 and s.count("**Aktiviti 2 (20 minit)")==1,n
card=(ROOT/"materials/pendidikan_moral/year6/unit_02_kad_aktiviti.md").read_text(encoding="utf-8")
assert all(x in card for x in ("Derma Darah","JKM","AADK/PPDa","DRAF_SEMAK"))
print("PASS 3/3 Year6 Unit2 source-text scene, SP, safety and historical provenance checks. Not visual release.")
