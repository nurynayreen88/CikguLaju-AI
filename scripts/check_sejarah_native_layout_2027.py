#!/usr/bin/env python3
"""Read-only unit contract: all Sejarah 2027 drafts shape a native Telegram layout.

It asserts public payload creation is still blocked for every lesson; this is
not a live Word/PDF delivery test or human approval.
"""
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from web.sejarah_2027_native_layout_adapter import internal_preview_layout, approved_native_payload
from web.sejarah_2027_staging_source import SejarahNotReady, preview_only

TEACHER={"class":"5 Amanah","date":"2027-03-22","time":"08:00-09:00"}
count=0
for y in (4,5,6):
    for n in range(1,37):
        r=preview_only(y,n)["rph"]
        layout=internal_preview_layout(y,n,TEACHER)
        assert layout["style"]=="telegram-native-rph-v1"
        assert 16<=len(layout["header"])<=22
        assert len({a["label"] for a in layout["header"]})==len(layout["header"])
        fields={a["label"]:a["value"] for a in layout["header"]}
        assert fields["MATA PELAJARAN"]=="Sejarah"
        assert fields["Standard Pembelajaran"]==", ".join(r["sp_codes"])
        assert fields["OBJEKTIF PEMBELAJARAN"]=="; ".join(r["objective"])
        assert fields["PENTAKSIRAN"]==r["pengukuhan_pbd"]["activity"]
        assert layout["activity_header"]==["Fasa / Masa","Aktiviti Pengajaran & Pembelajaran","Catatan"]
        assert len(layout["phases"])==3 and len(layout["footer"])==2
        main=layout["phases"][1]["activity"]
        assert all(r[k]["activity"] in main for k in ("aktiviti_1","aktiviti_2","pengukuhan_pbd"))
        assert r["set_induksi"]["activity"]==layout["phases"][0]["activity"]
        assert r["penutup"]["activity"]==layout["phases"][2]["activity"]
        assert layout["footer"][1]["value"]==r["reflection"]
        assert re.match(r"\d{2}:\d{2}-\d{2}:\d{2}",fields["MASA"])
        try:
            approved_native_payload(y,n,TEACHER,"word")
        except SejarahNotReady:
            pass
        else:
            raise AssertionError("Unapproved source reached native renderer")
        count+=1
assert count==108
print("Sejarah staging native-layout contract: 108 / 108 valid; all 108 public payloads BLOCKED")
