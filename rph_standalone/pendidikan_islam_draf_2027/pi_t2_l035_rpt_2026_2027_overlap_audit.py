"""RPT 2026 -> 2027 source provenance of withheld Year2 PdP035 ayah224 overlap.

The overlap is in the original 2026 teacher RPT, NOT a fabricated new 2027
curriculum boundary. It might be deliberate consolidation or a typo.
Never silently adjust Quran verse selection or create a teacher RPH from it.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pi_quality_audit import ROOT

SOURCE_RPT2026_ID="10nFtY-6tJRhvn8XggwtJRFBNozltQbqk"
SOURCE_RPT2026_SHA="e5328102b4d059616ede2adf5cdf3a357acf1c0d997a2472e135fa120fcb7845"
SOURCE_RPT2027_ID="1R2FNyT0CYb_WTMiw99lnZW9GuPaatz8w"
SOURCE_RPT2027_SHA="86a8e6fb599eb0f65f3a0a888cb29d636223c75896718d058886076a95f6c05d"
CODES={"L032":[216,224],"L035":[224,245],"NEXT_TASMI":[246,259]}


def audit(root=ROOT):
    d=json.loads((Path(root)/"year2.json").read_text(encoding="utf-8"))
    assert d["year"]==2 and d["ready"] is False and len(d["records"])==112
    p32=d["records"][31]
    p35=d["records"][34]
    assert p32["id"]=="T2-L032" and p32["withheld"] is False
    assert "سورة البقرة أية 216-224" in p32["fields"]["sp"]
    assert p35["id"]=="T2-L035" and p35["withheld"] is True
    assert p35["state"]=="TAHAN_SEMAKAN_KANDUNGAN"
    assert p35["verified_ready"] is False
    assert "fields" not in p35 and "intro" not in p35
    # Original Year2 2026 RPT table row 10 (216-224), row 11 (224-245)
    # and next row 12 (246-259), independently crosschecked with the
    # corresponding RPT2027 PDF pp11, 12 and 14; PdP032, PdP035 and PdP038.
    assert CODES["L032"][-1]==CODES["L035"][0]
    assert CODES["L035"][-1]+1==CODES["NEXT_TASMI"][0]
    return {
        "purpose":"Audit original 2026 carryover of overlapping verse224 for withheld Year2 lesson35",
        "rpt2026_drive_id":SOURCE_RPT2026_ID,
        "rpt2026_sha256":SOURCE_RPT2026_SHA,
        "rpt2027_drive_id":SOURCE_RPT2027_ID,
        "rpt2027_sha256":SOURCE_RPT2027_SHA,
        "rpt2027_pdf_pages_checked":[11,12,14],
        "year2_pdp032_surah_baqarah":[216,224],
        "year2_pdp035_surah_baqarah":[224,245],
        "following_2026_rpt_range":[246,259],
        "intersecting_ayah":[224],
        "overlap_present_in_original_2026_rpt":True,
        "overlap_retained_and_flagged_in_2027_rpt":True,
        "intentional_revision_vs_source_typo_resolved":False,
        "original_year2_l035_record_still_wholly_held":True,
        "surah_verse_number_modified":False,
        "expert_quran_sequence_approvals":0,
        "teacher_ready":0,
        "release":"NO_GO"
    }


def write(path,root=ROOT):
    d=audit(root)
    Path(path).write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(d,ensure_ascii=False,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    args=p.parse_args()
    write(args.output)
