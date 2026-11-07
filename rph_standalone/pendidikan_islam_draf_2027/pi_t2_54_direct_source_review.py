"""Source-bounded DSKP + textbook SP-footer crosswalk for PI Year 2 5.4.

A human read the user's Drive copies of the DSKP (printed p43, PDF p55)
and KSSR Semakan 2017 textbook (printed p134-138, PDF p144-148).
The source PDFs are NOT committed, downloaded or mirrored by CI.

This module asserts preserved originals plus two tightly scoped SK/SP wording
repairs in staging. It does NOT approve textbook exercises, Jawi spelling,
whole-lesson pedagogy, redistribution rights, or teacher publication.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

from pi_quality_audit import ROOT

TEXTBOOK_DRIVE_ID = "1VDXKCAyEveZCkhMLVVIyl3qg2sZhk9KP"
TEXTBOOK_SHA256 = "f9e2a3469c363cb233eb551d2a33c7979dbc836c7efa623e13046c74219ff654"
DSKP_DRIVE_ID = "1m6UG8t7tiCjLdnOo6vRj2jI4lNMniOUr"
DSKP_SHA256 = "dd4804c118e78c5a4fed1521adf750983c6d119a310cf736b751d4994bc67dac"
DSKP_PDF_PAGE = 55
DSKP_PRINTED_PAGE = 43
BOOK_PDF_OFFSET = 10

SP_BOOK_FOOTER_PAGES = {
    "5.4.1": [134, 137, 138],
    "5.4.2": [134, 138],
    "5.4.3": [135, 137],
    "5.4.4": [136, 138],
}
LESSON_CODES = {
    "T2-L102": ["5.4.1", "5.4.2"],
    "T2-L105": ["5.4.2", "5.4.3"],
    "T2-L108": ["5.4.3", "5.4.4"],
}
CORRECTED_IDS = {"T2-L105", "T2-L108"}
TEACHER_REFERENCE_PAGES = {
    "T2-L102": [134],
    "T2-L105": [134, 135],
    "T2-L108": [135, 136],
}
OLD_543 = "5.4.3 مڠاڤليكاسي ادب مڠاسيهي رسول الله"
NEW_543 = "5.4.3 مڠاڤليكاسي ادب٢ مڠاسيهي رسول الله"
OLD_OBJECTIVE_543 = "مڠاڤليكاسي ادب مڠاسيهي رسول الله"
NEW_OBJECTIVE_543 = "مڠاڤليكاسي ادب٢ مڠاسيهي رسول الله"

CSV_FIELDS = (
    "id", "target_sp_codes", "book_printed_pages_by_sp",
    "dskp_file_id", "dskp_pdf_page", "dskp_printed_page",
    "textbook_file_id", "textbook_sha256",
    "verified_book_sp_footer_correspondence",
    "source_supported_material_reference_pages", "source_original_material_line_preserved",
    "dskp_543_adab_adab_wording_corrected",
    "original_sk_sp_preserved", "original_objective_preserved",
    "activity_exact_page_verified", "jawi_editor_approved",
    "content_expert_approved", "rights_to_redistribute_book",
    "can_publish", "release"
)


def audit(root=ROOT):
    source = json.loads((Path(root) / "year2.json").read_text(encoding="utf-8"))
    if source["year"] != 2 or source["ready"] is not False or len(source["records"]) != 112:
        raise ValueError("Invalid original year2 records")
    allrows = {r["id"]: r for r in source["records"]}
    if {r["id"] for r in source["records"] if "staging_direct_dskp_book_crosswalk" in r} != set(LESSON_CODES):
        raise ValueError("Direct source crosswalk count / identity has drifted")
    rows = []
    for lesson_id, codes in LESSON_CODES.items():
        record = allrows[lesson_id]
        if record["withheld"] or record["verified_ready"] is not False:
            raise ValueError("Source content is not a withheld or published record")
        meta = record["staging_direct_dskp_book_crosswalk"]
        fields = record["fields"]
        if meta["evidence_id"] != "PI-T2-5.4-DSKP-TB-20261107":
            raise ValueError("Evidence version changed")
        assert meta["direct_visual_evidence_reviewed"] is True
        assert meta["book_footer_sp_crosswalk_checked"] is True
        assert meta["textbook_source_drive_file_id"] == TEXTBOOK_DRIVE_ID
        assert meta["dskp_source_drive_file_id"] == DSKP_DRIVE_ID
        assert meta["dskp_pdf_page"] == DSKP_PDF_PAGE
        assert meta["dskp_printed_page"] == DSKP_PRINTED_PAGE
        assert meta["textbook_sp_footer_pdf_page_offset"] == BOOK_PDF_OFFSET
        assert meta["lesson_sp_codes_observed_on_dskp_page"] == codes
        assert meta["textbook_sp_footer_printed_pages"] == {
            code: SP_BOOK_FOOTER_PAGES[code] for code in codes
        }
        assert meta["textbook_page_claim_original_unmodified"] is True
        assert record["staging_textbook_toc_correction"]["publication"] == "HOLD"
        assert "ms. 133–140" in fields["bahan"]
        material = meta["material_page_guidance"]
        assert material["textbook_printed_pages_observed"] == TEACHER_REFERENCE_PAGES[lesson_id]
        assert material["original_materials_first_line"] == (
            "Kad situasi adab, gambar contoh tingkah laku, senarai semak pemerhatian"
        )
        assert material["draft_materials_first_line"] == fields["bahan"].splitlines()[0]
        assert material["draft_materials_first_line"].startswith(
            material["original_materials_first_line"]+"; Buku Teks PI Tahun 2 ms. "
        )
        assert material["original_audit_note_preserved"] is True
        assert material["textbook_reference_only_not_pdf_copy"] is True
        assert material["exercise_or_pbd_verified"] is False
        assert material["full_content_expert_approved"] is False
        assert material["publication"] == "HOLD"
        original_sp = meta["original_sp_preserved"]
        original_obj = meta["original_objective_preserved"]
        assert isinstance(original_sp, str) and isinstance(original_obj, str)
        for code in codes:
            assert f"{code} " in fields["sp"]
            assert f"{code} " in original_sp
        correction = lesson_id in CORRECTED_IDS
        assert meta["dskp_sp_5_4_3_plural_wording_correction"] is correction
        if correction:
            assert OLD_543 in original_sp and NEW_543 in fields["sp"]
            assert NEW_543 not in original_sp and OLD_543 not in fields["sp"]
            assert OLD_OBJECTIVE_543 in original_obj
            assert NEW_OBJECTIVE_543 in fields["objektif"]
            assert fields["sp"] == original_sp.replace(OLD_543, NEW_543)
            assert fields["objektif"] == original_obj.replace(OLD_OBJECTIVE_543, NEW_OBJECTIVE_543)
        else:
            assert fields["sp"] == original_sp
            assert fields["objektif"] == original_obj
        for key in (
            "lesson_specific_activity_and_exercise_approved",
            "source_rights_for_distribution_approved",
            "full_lesson_content_expert_approved",
            "jawi_orthography_approved",
        ):
            assert meta[key] is False
        assert meta["publication"] == "HOLD"
        rows.append({
            "id": lesson_id,
            "target_sp_codes": "|".join(codes),
            "book_printed_pages_by_sp": json.dumps(
                {k: SP_BOOK_FOOTER_PAGES[k] for k in codes}, ensure_ascii=False
            ),
            "dskp_file_id": DSKP_DRIVE_ID,
            "dskp_pdf_page": DSKP_PDF_PAGE,
            "dskp_printed_page": DSKP_PRINTED_PAGE,
            "textbook_file_id": TEXTBOOK_DRIVE_ID,
            "textbook_sha256": TEXTBOOK_SHA256,
            "verified_book_sp_footer_correspondence": True,
            "source_supported_material_reference_pages": "|".join(str(x) for x in TEACHER_REFERENCE_PAGES[lesson_id]),
            "source_original_material_line_preserved": True,
            "dskp_543_adab_adab_wording_corrected": correction,
            "original_sk_sp_preserved": bool(original_sp),
            "original_objective_preserved": bool(original_obj),
            "activity_exact_page_verified": False,
            "jawi_editor_approved": False,
            "content_expert_approved": False,
            "rights_to_redistribute_book": False,
            "can_publish": False,
            "release": "NO_GO",
        })
    assert len(rows) == 3 and sum(x["dskp_543_adab_adab_wording_corrected"] for x in rows) == 2
    assert sum(x["verified_book_sp_footer_correspondence"] for x in rows) == 3
    return {
        "purpose": "Original DSKP p43 and textbook p134-138 SP footer preflight; editorial only",
        "dskp_file_id": DSKP_DRIVE_ID,
        "dskp_sha256": DSKP_SHA256,
        "textbook_file_id": TEXTBOOK_DRIVE_ID,
        "textbook_sha256": TEXTBOOK_SHA256,
        "dskp_sp_codes_observed": sorted(SP_BOOK_FOOTER_PAGES),
        "book_printed_pages_by_sp": SP_BOOK_FOOTER_PAGES,
        "book_page_to_pdf_offset": BOOK_PDF_OFFSET,
        "directly_cross_checked_lesson_count": 3,
        "sp_543_jawi_wording_corrections": 2,
        "staging_rph_material_book_page_references_added": 3,
        "book_sp_footer_page_evidence_count": 5,
        "lesson_specific_activity_approvals": 0,
        "jawi_expert_approvals": 0,
        "academic_quality_score": None,
        "can_publish": False,
        "release": "NO_GO",
        "rows": rows,
    }


def write(json_path, csv_path, root=ROOT):
    result = audit(root)
    Path(json_path).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
    with Path(csv_path).open("w", encoding="utf-8-sig", newline="") as dest:
        wr = csv.DictWriter(dest, fieldnames=CSV_FIELDS)
        wr.writeheader()
        wr.writerows(result["rows"])
    print(json.dumps({k: v for k, v in result.items() if k != "rows"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    write(args.json, args.csv)
