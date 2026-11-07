"""Year 3 Awalan (Jawi) original textbook page evidence; staging only.

Inspected Drive source GuruBesar_BukuTeks_Pendidikan_Islam_T3_SK.pdf
(PDF pages 31-33, each two-page spread; printed pp46-51).
The next PDF page 34 starts the Akhiran unit; six legacy PDF34 candidate
notes are therefore overbroad. Existing note is *preserved*, never silently
converted into a verified book exercise citation.

SP7.1.1 reading and SP7.1.2 writing have observed footer tags on
this Awalan unit; the specific prefixes/examples assigned per individual RPH
still require teacher/editor review. No textbook PDF is copied to GitHub.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

from pi_quality_audit import ROOT

DRIVE_SOURCE = "1DNXL1vmN3ERz6o4_7jcCVc9m3E42JDSY"
SOURCE_SHA256 = "fcc36cbe9ed64aa7d8cbf17dbf105b73c2e34e4fc988e65d63a12fa2386a4f17"
READING = frozenset({"T3-L004","T3-L008","T3-L012","T3-L016","T3-L020","T3-L024"})
WRITING = frozenset({"T3-L028","T3-L032","T3-L036","T3-L040","T3-L044","T3-L048"})
ORIGINAL_MATERIAL = "Kad huruf/perkataan Jawi, petikan atau kad ayat, alat tulis"
CSV_FIELDS=(
    "id","sp_code","printed_pages_for_unit","book_pdf_spread_pages",
    "textbook_file_id","textbook_sha256",
    "original_materials_preserved","exact_sk_sp_unchanged",
    "legacy_pdf_page34_wrong_unit","source_footer_sp_code_observed",
    "specific_rph_prefix_examples_verified",
    "textbook_exercise_or_pbd_approved","dskp_full_text_verified",
    "jawi_orthography_approved","content_expert_approved",
    "can_publish","release"
)


def audit(root=ROOT):
    data=json.loads((Path(root)/"year3.json").read_text(encoding="utf-8"))
    assert data["year"] == 3 and data["ready"] is False and len(data["records"]) == 147
    rows=[]
    seen=set()
    for record in data["records"]:
        if "staging_direct_book_awalan" not in record:
            continue
        identity=record["id"]
        if identity in seen or identity not in READING|WRITING:
            raise ValueError("Unexpected book-reference identity " + identity)
        seen.add(identity)
        is_read=identity in READING
        expected_sp="7.1.1" if is_read else "7.1.2"
        expected_pages=list(range(46,52)) if is_read else [49,50,51]
        expected_pdf=[31,32,33] if is_read else [32,33]
        old=record["staging_direct_book_awalan"]
        fields=record["fields"]
        if not fields["sp"].startswith(expected_sp):
            raise ValueError("SP code mismatch "+identity)
        if not record["verified_ready"] is False or record["withheld"]:
            raise ValueError("Draft status drift "+identity)
        assert old["evidence_id"]=="PI-T3-AWALAN-TB-P46-51-20261107"
        assert old["textbook_source_drive_file_id"]==DRIVE_SOURCE
        assert old["textbook_sha256"]==SOURCE_SHA256
        assert old["printed_unit_page_range"]==[46,51]
        assert old["printed_reference_pages_used"]==expected_pages
        assert old["pdf_source_spread_pages"]==expected_pdf
        assert old["sp_code_in_textbook_footer"]==expected_sp
        assert old["source_sk_sp_unchanged"] is True
        original=old["old_bahan_full_preserved"]
        original_first, original_note=original.split("\n",1)
        assert original_first==ORIGINAL_MATERIAL
        assert "Rekod padanan SP buku teks lama wujud; halaman PDF calon " in original_note
        assert fields["bahan"].split("\n",1)[1]==original_note
        assert old["legacy_pdf_page34_refers_to_next_akhiran_unit"] is is_read
        if is_read:
            assert "34 (BELUM" in original_note
        new_first=fields["bahan"].split("\n",1)[0]
        assert new_first==old["material_reference_added_to_first_line"]
        expected_text="46–51" if is_read else "49–51"
        assert new_first==ORIGINAL_MATERIAL+(
            f"; Buku Teks PI Tahun 3 ms. {expected_text} (Jawi: imbuhan awalan; rujukan unit sahaja)"
        )
        for k in ("exact_lesson_prefix_examples_verified",
                  "specific_book_activity_exercise_approved",
                  "dskp_full_text_crosschecked",
                  "content_expert_approved","jawi_orthography_approved",
                  "pdf_redistribution_rights_verified"):
            assert old[k] is False, (identity,k)
        assert old["publication"]=="HOLD"
        rows.append({
            "id":identity,
            "sp_code":expected_sp,
            "printed_pages_for_unit":"|".join(map(str,expected_pages)),
            "book_pdf_spread_pages":"|".join(map(str,expected_pdf)),
            "textbook_file_id":DRIVE_SOURCE,
            "textbook_sha256":SOURCE_SHA256,
            "original_materials_preserved":True,
            "exact_sk_sp_unchanged":True,
            "legacy_pdf_page34_wrong_unit":is_read,
            "source_footer_sp_code_observed":True,
            "specific_rph_prefix_examples_verified":False,
            "textbook_exercise_or_pbd_approved":False,
            "dskp_full_text_verified":False,
            "jawi_orthography_approved":False,
            "content_expert_approved":False,
            "can_publish":False,
            "release":"NO_GO",
        })
    assert seen==READING|WRITING and len(rows)==12
    assert sum(x["legacy_pdf_page34_wrong_unit"] for x in rows)==6
    assert sum(x["source_footer_sp_code_observed"] for x in rows)==12
    return {
        "purpose":"Original Year 3 Awalan unit printed-page guidance ONLY, not lesson/prefix accreditation",
        "textbook_drive_id":DRIVE_SOURCE,
        "source_sha256":SOURCE_SHA256,
        "book_pdf_spreads_inspected":[31,32,33,34],
        "book_printed_awalan_pages":[46,47,48,49,50,51],
        "year3_awalan_lessons_with_direct_book_unit_reference":12,
        "year3_awalan_reading_lessons":6,
        "year3_awalan_writing_lessons":6,
        "legacy_pdf_page34_hints_wrong_next_unit":6,
        "specific_lesson_prefix_examples_approved":0,
        "dskp_full_text_verified":0,
        "expert_approved":0,
        "can_publish":False,
        "release":"NO_GO",
        "rows":rows,
    }


def write(json_path,csv_path,root=ROOT):
    d=audit(root)
    Path(json_path).write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with Path(csv_path).open("w",newline="",encoding="utf-8-sig") as dst:
        w=csv.DictWriter(dst,fieldnames=CSV_FIELDS)
        w.writeheader();w.writerows(d["rows"])
    print(json.dumps({k:v for k,v in d.items() if k!="rows"},ensure_ascii=False,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--json",required=True)
    p.add_argument("--csv",required=True)
    a=p.parse_args()
    write(a.json,a.csv)
