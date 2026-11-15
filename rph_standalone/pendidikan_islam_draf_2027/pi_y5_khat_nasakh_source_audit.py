"""KSSR mainstream Year5 khat Nasakh SP numbering source audit (HOLD).

The official KPM DSKP Tahun 5 in project Drive, printed pp43–44, identifies:
7.2.3 huruf, 7.2.4 perkataan, 7.2.5 ayat mudah, 7.2.6 amalan tekal.
Four inherited source RPH rows used incorrect numbers and an objective mismatch.
Only the four *staging* records are source-aligned; teacher approval is pending.
Never conflate this mainstream KSSR with the separate KSSRPK DSKP.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path

from pi_quality_audit import ROOT, COUNT

DSKP_DRIVE_ID = "1P6ClIlwU1OFd3tEUdoKt3VnAAGGbpja6"
UPDATED = {"T5-L131","T5-L135","T5-L139","T5-L143"}
LETTER = {"T5-L092","T5-L096","T5-L100","T5-L104"}
WORD = {"T5-L111","T5-L115","T5-L119","T5-L123","T5-L127"}
SP_OLD="7.2.4 منوليس ايات موده مڠيكوت قاعده خط نسخ.\n7.2.5 ممبوداياكن ڤنوليسن خط سچارا تكل."
SP_NEW="7.2.5 منوليس ايات موده مڠيكوت قاعده خط نسخ.\n7.2.6 ممبوداياكن ڤنوليسن خط سچارا تكل."
OBJ_OLD="1. منوليس ڤركاتاءن مڠيكوت قاعده خط نسخ يڠ بتول."
OBJ_NEW="1. منوليس ايات موده مڠيكوت قاعده خط نسخ يڠ بتول."

def audit(root=ROOT):
    root=Path(root)
    data=json.loads((root/"year5.json").read_text(encoding="utf-8"))
    assert data["ready"] is False and data["year"]==5
    assert len(data["records"])==COUNT[5]==143
    records={x["id"]:x for x in data["records"]}
    assert len(records)==143
    rows=[]
    for ident in sorted(UPDATED):
        row=records[ident]
        assert not row["withheld"] and row["verified_ready"] is False
        f=row["fields"]
        m=row["staging_y5_khat_nasakh_dskp_sp_correction"]
        assert f["sp"]==SP_NEW and OBJ_NEW in f["objektif"]
        assert OBJ_OLD not in f["objektif"]
        assert m["revision"]=="pi-year5-khat-nasakh-dskp-sp-20261108"
        assert m["original_fields"]["sp"]==SP_OLD
        assert OBJ_OLD in m["original_fields"]["objektif"]
        assert m["revised_fields"]=={"sp":f["sp"],"objektif":f["objektif"]}
        assert m["primary_source_file_id"]==DSKP_DRIVE_ID
        assert m["primary_source_printed_pages"]==[43,44]
        assert m["source_sp_sequence"]=={
            "7.2.4":"menulis perkataan khat Nasakh",
            "7.2.5":"menulis ayat mudah khat Nasakh",
            "7.2.6":"membudayakan penulisan khat secara tekal",
        }
        assert m["original_source_sha256_preserved"] is True
        assert m["source_activity_and_pbd_unchanged"] is True
        assert m["outside_source_rpt_modified"] is False
        assert m["academic_expert_approved"] is False
        assert m["jawi_orthography_approved"] is False
        assert m["teacher_ready"] is False and m["publication"]=="HOLD"
        assert isinstance(row["source_sha256"],str) and len(row["source_sha256"])==64
        rows.append({"id":ident,"corrected_sp_codes":["7.2.5","7.2.6"],
                     "objective_matches_ayat":True,"source_pages":[43,44],
                     "original_preserved":True,"expert_approved":False,
                     "teacher_ready":False})
    for ident in sorted(LETTER):
        sp=records[ident]["fields"]["sp"]
        assert "7.2.3 منوليس حروف" in sp and "7.2.2" in sp
    for ident in sorted(WORD):
        sp=records[ident]["fields"]["sp"]
        assert "7.2.4 منوليس ڤركاتاءن" in sp and "7.2.2" in sp
    for row in data["records"]:
        if row["withheld"]: continue
        sp=row["fields"]["sp"]
        assert "7.2.4 منوليس ايات موده" not in sp, row["id"]
        assert "7.2.5 ممبوداياكن" not in sp, row["id"]
    return {
        "subject":"Pendidikan Islam","year":5,
        "source_file_id":DSKP_DRIVE_ID,"source_printed_pages":[43,44],
        "four_corrected_ayat_and_tekal_sp_records":len(rows),
        "letter_sp_unchanged":len(LETTER),
        "word_sp_unchanged":len(WORD),
        "source_year5_records":len(records),
        "original_fields_preserved":True,
        "original_source_rpt_changed":False,
        "academic_expert_approvals":0,
        "year5_khat_ready":0,
        "release":"NO_GO",
        "rows":rows,
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    args=p.parse_args()
    result=audit()
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
