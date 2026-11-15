"""Year4 L083 source-excerpt repair with original DSKP/book evidence.

Manual visual source readings:
- DSKP PI Y4 printed p27 / PDF p39: SP2.1.1, abbreviated hadith excerpt.
- Buku Teks PI Y4 printed p51 / PDF p57: corresponding matan with narrator.
We intentionally retain the DSKP's leading ellipsis: this is the excerpt used
in the source standard, NOT a claim to reproduce the entire narrated hadith.
The lesson stays critical HOLD until academic/Jawi experts approve.
This CI module does not download source PDFs or distribute book images.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pi_quality_audit import ROOT

LESSON_ID="T4-L083"
BOOK_ID="17x1icc3hkoutTopyjbyi6kIfmxksBo1R"
BOOK_SHA256="dfcd7720c1adc7c6aaec6cfae55ea66a2db2605288359d4f10acef2000ad7451"
DSKP_ID="1r5IexeLxm5L025Abj_V-r6NRlDBeoQdJ"
DSKP_SHA256="e30b48edf947002afb466605d8c3375e2876265dcfb73c2161f0e0416669351b"
EXCERPT="... وَمَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الْآخِرِ فَلْيُكْرِمْ ضَيْفَهُ"


def audit(root=ROOT):
    d=json.loads((Path(root)/"year4.json").read_text(encoding="utf-8"))
    assert d["year"]==4 and d["ready"] is False and len(d["records"])==151
    rows=[r for r in d["records"] if "staging_hadith_original_source_verified" in r]
    assert len(rows)==1 and rows[0]["id"]==LESSON_ID
    r=rows[0]
    meta=r["staging_hadith_original_source_verified"]
    fields=r["fields"];original=meta["original_fields_preserved"]
    assert r["verified_ready"] is False and r["withheld"] is False
    assert r["staging_source_review_required"] is True
    assert meta["revision"]=="pi-t4-l083-book51-dskp27-20261107"
    assert meta["source_book_drive_id"]==BOOK_ID
    assert meta["source_book_sha256"]==BOOK_SHA256
    assert meta["source_book_pdf_page"]==57 and meta["source_book_printed_page"]==51
    assert meta["source_dskp_drive_id"]==DSKP_ID
    assert meta["source_dskp_sha256"]==DSKP_SHA256
    assert meta["source_dskp_pdf_page"]==39 and meta["source_dskp_printed_page"]==27
    assert EXCERPT==meta["source_excerpt_used"]
    assert meta["dskp_excerpt_ellipsis_preserved"] is True
    assert meta["source_excerpt_not_full_hadith_narration"] is True
    assert meta["matan_excerpt_page_directly_verified"] is True
    assert "قال رسول الله :" in original["sp"]
    assert "قال رسول الله :\n   \n" in original["sp"]
    assert EXCERPT not in original["sp"]
    assert fields["sp"].count(EXCERPT)==1
    assert fields["sp"].startswith("2.1.1")
    assert "رواه البخاري ومسلم" in fields["sp"]
    assert "ممولي" in fields["sp"]
    assert fields["sk"]==original["sk"] and fields["penutup"]==original["penutup"]
    assert fields["bahan"].split("\n",1)[1]==original["bahan"].split("\n",1)[1]
    assert "ms. 51" in fields["bahan"].split("\n")[0]
    assert len(original["aktiviti_utama"].splitlines())==1
    assert len(fields["aktiviti_utama"].splitlines())==3
    assert "1. " in fields["aktiviti_utama"] and "2. " in fields["aktiviti_utama"]
    assert "3. " in fields["aktiviti_utama"]
    assert "سواݢ ستهلا" not in fields["aktiviti_utama"]
    assert "ممبتولكن سبوتن دان فهمن موريد" in fields["aktiviti_utama"]
    assert "ڤبد اينديويدو:" in fields["pentaksiran"]
    assert "تتامو" in fields["pentaksiran"]
    assert "تتامو" in fields["objektif"]
    assert "بخيل" not in fields["pentaksiran"]
    for k in ("source_sk_heading_unchanged","exact_dskp_sp_wording_approved",
              "expert_hadith_text_review_approved","pedagogical_content_expert_approved",
              "jawi_orthography_approved","native_word_pdf_visual_approved"):
        assert meta[k] is (k=="source_sk_heading_unchanged"),k
    assert meta["publication"]=="HOLD"
    return {
      "purpose":"One Year4 hadith book/DSKP excerpt restored in staging, no expert approval",
      "lesson_id":LESSON_ID,
      "book_drive_id":BOOK_ID,
      "book_sha256":BOOK_SHA256,
      "book_pdf_page":57,
      "book_printed_page":51,
      "dskp_drive_id":DSKP_ID,
      "dskp_sha256":DSKP_SHA256,
      "dskp_pdf_page":39,
      "dskp_printed_page":27,
      "staging_source_excerpt_recovered":1,
      "complete_original_narration_certified":0,
      "physical_activity_steps_after_repair":3,
      "source_missing_critical_flag_still_holds":True,
      "expert_hadith_approvals":0,
      "jawi_orthography_approvals":0,
      "academic_quality_percent":None,
      "can_publish":False,
      "release":"NO_GO"
    }


def write(path,root=ROOT):
    d=audit(root)
    Path(path).write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(d,ensure_ascii=False,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    args=p.parse_args();write(args.output)
