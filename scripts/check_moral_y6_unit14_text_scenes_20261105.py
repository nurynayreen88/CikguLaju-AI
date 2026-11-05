#!/usr/bin/env python3
"""Text-scene check; does not certify full visual book or real teacher delivery."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/"audits/pendidikan_moral_y6_unit14_text_scenes_20261105.json").read_text(encoding="utf-8"))
assert data["level"]=="TEXTUAL_ACTIVITIES_ONLY_NOT_FULL_VISUAL"
phrases={40:["Tahun Baharu Cina","Thaipusam","rombongan pengantin","SP 14.1–14.2"],41:["GPI","2020","risalah","SP 14.3–14.4"],42:["risalah","ucapan","m/s 140","SP 14.5"]}
for n,tokens in phrases.items():
    s=(root/f"rph_standalone/pendidikan_moral/year6/lesson_{n:03d}.md").read_text(encoding="utf-8")
    assert all(x in s for x in tokens),(n,tokens)
    assert "DRAF SEMAK" in s and "Padanan bab edisi Semakan 2017" in s
s=(root/"materials/pendidikan_moral/year6/unit_14_kad_aktiviti.md").read_text(encoding="utf-8")
assert "DRAF_SEMAK" in s and "GPI 2020" in s
print("PASS 3 Unit14 textual scene links, historic GPI context, original SPs and DRAF status.")
