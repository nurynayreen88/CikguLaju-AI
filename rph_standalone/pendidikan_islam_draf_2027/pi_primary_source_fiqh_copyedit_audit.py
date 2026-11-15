"""Source-grounded Year4 fasting correction and three exact verb typo fixes.

Year4 official KPM student book p.130 (Drive id below) identifies TWO
rukun puasa: niat, abstaining from invalidating acts. The inherited 2027
RPT Year4 PdP107 incorrectly asks for SIX rukun puasa. Do not publish
that factual error; original source PDF and all DB/runtime fields untouched.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pi_quality_audit import COUNT, ROOT

BOOK_ID="17x1icc3hkoutTopyjbyi6kIfmxksBo1R"
RPT_ID="1O7Jvuvs7B7CF1tomvJdBTo7khSnu2haX"
VERB_REPAIRS=("T4-L103","T5-L103","T5-L138")


def audit(root=ROOT):
    root=Path(root)
    records={}
    for y,n in COUNT.items():
        o=json.loads((root/f"year{y}.json").read_text(encoding="utf-8"))
        assert len(o["records"])==n and o["ready"] is False
        for row in o["records"]:
            records[row["id"]]=row
    assert len(records)==696
    row=records["T4-L107"]
    f=row["fields"]; meta=row["staging_fiqh_year4_puasa_two_pillars_source_correction"]
    assert row["verified_ready"] is False and not row["withheld"]
    assert "4.3.3" in f["sp"] and "4.3.4" in f["sp"]
    assert "مثنارايكن 6 درڤد روكون ڤواسا رمضان" in meta["original_fields"]["objektif"]
    assert "مثنارايكن 2 روكون ڤواسا رمضان" in f["objektif"]
    assert "جادوال ڤربيذاءن روكون دان عملن سنة ڤواسا رمضان" in f["aktiviti_utama"]
    assert meta["textbook_drive_id"]==BOOK_ID and meta["textbook_printed_page"]==130
    assert meta["rpt2027_drive_id"]==RPT_ID
    assert len(meta["textbook_findings"])==2
    assert meta["source_sp_unchanged"] and meta["outside_source_rpt_modified"] is False
    assert meta["fiqh_expert_approved"] is False and meta["publication"]=="HOLD"
    assert not any(
        "6 درڤد روكون ڤواسا" in str(x.get("fields",{}))
        for x in records.values()
    )
    rows=[]
    for ident in VERB_REPAIRS:
        x=records[ident]
        m=x["staging_exact_duplicate_verb_copyedit"]
        assert x["verified_ready"] is False
        assert "مثاتاكن مثاتاكن" in m["original_objektif"]
        assert "مثاتاكن مثاتاكن" not in x["fields"]["objektif"]
        assert x["fields"]["objektif"]==m["revised_objektif"]
        assert m["sk_sp_untouched"] is True
        assert m["publication"]=="HOLD"
        assert m["academic_expert_approved"] is False
        rows.append({"id":ident,"change":"remove one duplicated Jawi verb",
                     "original_saved":True,"published":False})
    return {
        "scope":"PI Year4 fasting source contradiction and 3 Jawi objective copyedits",
        "original_rpt_year4_pdp107_six_rukun_incorrect":True,
        "kpm_year4_textbook_source_id":BOOK_ID,
        "source_book_page_printed":130,
        "two_rukun_puasa_correction_applied_in_staging":True,
        "source_sp_modified":False,
        "other_exact_word_duplicate_fixes":len(rows),
        "other_verified_fiqh_claims":0,
        "expert_fiqh_approved":False,
        "expert_jawi_approved":False,
        "teacher_release":False,
        "release":"NO_GO",
        "rows":[{"id":"T4-L107","change":"correct six fasting pillars to two in objective",
                 "source_page":130,"original_saved":True,"published":False},*rows]
    }

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    r=audit()
    Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in r.items() if k!="rows"},ensure_ascii=False,indent=2))
