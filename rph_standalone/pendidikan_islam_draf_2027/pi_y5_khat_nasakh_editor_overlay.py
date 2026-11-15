"""Year 5 khat Nasakh: 13 specific editor-only RPH improvements.

Replace unsupported 'Buku Aktiviti' claims in restricted reviewer previews with
teacher-created exercise sheets, and align PBD observable evidence to the exact
SP skill: huruf, perkataan, or ayat mudah/tekal. Full source fields and hashes
remain available; no official workbook page is invented or offered to teachers.
Jawi orthography and detailed pedagogy must be approved before publication.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from pi_quality_audit import ROOT
from pi_y5_activity_book_wording_review import EXPECTED as SOURCE_MENTIONS
from pi_y5_khat_nasakh_source_audit import LETTER, WORD, UPDATED, audit as source_audit

SHEET="لمبارن لاتيهن يڠ دسدياكن ݢورو"
MATERIAL="Pen khat/kalam, kertas bergaris, kad contoh khat Nasakh, senarai semak bentuk huruf dan jarak tulisan."

def generate(root=ROOT):
    root=Path(root)
    src=source_audit(root)
    assert src["four_corrected_ayat_and_tekal_sp_records"]==4
    assert src["release"]=="NO_GO"
    doc=json.loads((root/"year5.json").read_text(encoding="utf-8"))
    assert doc["ready"] is False and len(doc["records"])==143
    assert set(SOURCE_MENTIONS)==LETTER|WORD|UPDATED
    rows=[]
    for r in doc["records"]:
        ident=r["id"]
        if ident not in SOURCE_MENTIONS:continue
        assert not r["withheld"] and r["verified_ready"] is False
        fields=r["fields"]
        source_field=SOURCE_MENTIONS[ident]
        orig=fields[source_field]
        assert orig.count("بوكو اكتيۏيتي")==1,(ident,orig)
        before={key:fields[key] for key in ("sk","sp","objektif","aktiviti_utama","pentaksiran","bahan")}
        updated=dict(before)
        if ident in LETTER:
            assert source_field=="pentaksiran"
            assert "7.2.3 منوليس حروف" in fields["sp"]
            examples=fields["sp"].splitlines()[-1].strip()
            assert 6<=len(examples.split())<=7
            kind="HURUF"
            pbd=(f"ڤبد اينديويدو: موريد منوليس حروف {examples} دالم خط نسخ ڤد {SHEET}. "
                 "ݢورو مڽمق بنتوق حروف، جرق دان ڤڠݢوناءن الات خط؛ "
                 "تيندقن سوسولن دريكود.")
        elif ident in WORD:
            assert source_field=="pentaksiran"
            assert "7.2.4 منوليس ڤركاتاءن" in fields["sp"]
            examples=fields["sp"].splitlines()[-1].strip()
            assert len(examples.split(" – "))>=5
            kind="PERKATAAN"
            pbd=(f"ڤبد اينديويدو: موريد منوليس ڤركاتاءن {examples} دالم خط نسخ ڤد {SHEET}. "
                 "ݢورو مڽمق سامبوڠن حروف، جرق دان ككمسن؛ "
                 "تيندقن سوسولن دريكود.")
        else:
            assert ident in UPDATED
            assert source_field=="aktiviti_utama"
            assert "7.2.5 منوليس ايات موده" in fields["sp"]
            assert "7.2.6 ممبوداياكن" in fields["sp"]
            assert "1. منوليس ايات موده" in fields["objektif"]
            examples=None
            kind="AYAT_DAN_TEKAL"
            pbd=(f"ڤبد اينديويدو: موريد منوليس ايات موده يڠ دتنتوكن ݢورو دالم خط نسخ ڤد {SHEET}. "
                 "ݢورو مڽمق جرق انتارا ڤركاتاءن دان ككمسن، سرتا مريكود "
                 "عملن برلاتيه سچارا تكل. ڤڠواساءن SP 7.2.5 دان 7.2.6 "
                 "دسمق دالم ببراڤ سيسي.")
            steps=fields["aktiviti_utama"].splitlines()
            assert len(steps)==3 and steps[1].startswith("2. ") and steps[1].count("بوكو اكتيۏيتي")==1
            steps[1]=(f"2. ݢورو مڽدياكن ساتو ايات موده ڤد كاد چونتوه؛ موريد "
                      f"منوليسڽ دالم خط نسخ ڤد {SHEET}، دان ݢورو مڽمق "
                      "سوسونن حروف دان جرق انتارا ڤركاتاءن.")
            updated["aktiviti_utama"]="\n".join(steps)
        updated["pentaksiran"]=pbd
        updated["bahan"]=MATERIAL
        assert "بوكو اكتيۏيتي" not in updated["pentaksiran"]
        assert "بوكو اكتيۏيتي" not in updated["aktiviti_utama"]
        assert updated["sp"]==before["sp"] and updated["objektif"]==before["objektif"]
        assert updated["sk"]==before["sk"]
        assert updated[source_field]!=before[source_field]
        changed={k:{"before":before[k],"after":updated[k],
                    "before_sha256":hashlib.sha256(before[k].encode("utf-8")).hexdigest()}
                 for k in ("aktiviti_utama","pentaksiran","bahan") if before[k]!=updated[k]}
        assert len(changed)==(3 if kind=="AYAT_DAN_TEKAL" else 2)
        rows.append({
          "id":ident,"year":5,"lesson":r["lesson"],"domain":"JAWI_KHAT_NASAKH",
          "type":kind,"source_examples_from_sp":examples,
          "source_sk_unchanged":before["sk"],
          "source_sp_unchanged":before["sp"],
          "source_objective_unchanged":before["objektif"],
          "revised_fields":updated,
          "original_fields":before,
          "changes":changed,
          "unsupported_source_book_reference":"بوكو اكتيۏيتي",
          "official_buku_aktiviti_edition_or_page_confirmed":False,
          "teacher_prepared_worksheet_only":True,
          "academic_content_approved":False,
          "jawi_spelling_approved":False,
          "source_catalog_overwritten":False,
          "can_publish":False,
          "release":"NO_GO",
        })
    assert len(rows)==13 and len({r["id"] for r in rows})==13
    assert sum(x["type"]=="HURUF" for x in rows)==4
    assert sum(x["type"]=="PERKATAAN" for x in rows)==5
    assert sum(x["type"]=="AYAT_DAN_TEKAL" for x in rows)==4
    assert sum(len(x["changes"]) for x in rows)==30
    assert all(x["revised_fields"]["sp"]==x["original_fields"]["sp"] and
               x["revised_fields"]["objektif"]==x["original_fields"]["objektif"] and
               x["can_publish"] is False for x in rows)
    return {
      "scope":"PI Year5 13 khat Nasakh RPH editor previews only",
      "source_rph_count":143,"editor_proposed_improvements":13,
      "sp_source_corrected_prior_to_overlay":4,
      "original_activity_book_mentions_retained_in_provenance":13,
      "preview_unsupported_official_activity_book_mentions":0,
      "new_source_verified_workbook_pages":0,
      "editor_changed_field_count":30,
      "original_json_modified_by_overlay":False,
      "jawi_expert_approvals":0,"teacher_ready":0,
      "release":"NO_GO","rows":rows,
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    args=p.parse_args()
    r=generate()
    Path(args.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in r.items() if k!="rows"},ensure_ascii=False,indent=2))
