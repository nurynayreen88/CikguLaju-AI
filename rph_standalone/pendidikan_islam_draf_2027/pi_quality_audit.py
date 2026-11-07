"""Conservative staging QA for Pendidikan Islam 2027 drafts.
Content-quality percentage MUST NOT be inferred from formatting or inventory.
No runtime imports; no writes to database, Telegram or Web.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import json
import re

ROOT = Path(__file__).resolve().parent
COUNT = {2: 112, 3: 147, 4: 151, 5: 143, 6: 143}
HELD = {(2, 35), (6, 6), (6, 14), (6, 18), (6, 60), (6, 117)}
REQUIRED = ("sk", "sp", "objektif", "set_induksi", "aktiviti_utama",
            "pentaksiran", "penutup", "bahan")
STATES = {"CALON_UJIAN_GURU_DRAF", "SEMAKAN_KEUTAMAAN",
          "TAHAN_SEMAKAN_KANDUNGAN"}
NUMBERED = re.compile(r"^\s*([0-9]{1,2})[.)]\s+", re.ASCII)
UNVERIFIED_PAGE = ("perlu padanan", "padanan sk/toc terdahulu",
                   "halaman khusus belum", "belum dipadankan")
# Reused generic PBD statement. Detect for editorial triage; do not auto-fill.
GENERIC_PBD = "برداسركن كريتيريا دالم SP"
DOMAINS = {"القرءان": "al-Quran", "جاوي": "Jawi", "عقيدة": "Akidah",
           "عبادة": "Ibadah", "سيرة": "Sirah", "ادب": "Adab",
           "حديث": "Hadis"}


def audit(root=ROOT):
    """Identify edit targets and block unsupported academic quality claims."""
    rows = []
    seen = set()
    for year, expected in COUNT.items():
        payload = json.loads((Path(root) / f"year{year}.json").read_text(encoding="utf-8"))
        assert payload["year"] == year and payload["ready"] is False
        assert len(payload["records"]) == expected
        for lesson, record in enumerate(payload["records"], 1):
            key = (year, lesson)
            assert key not in seen
            seen.add(key)
            assert record["id"] == f"T{year}-L{lesson:03}"
            assert record["lesson"] == lesson and record["tahun"] == year
            assert record["state"] in STATES and record["verified_ready"] is False
            held = key in HELD
            assert record["withheld"] is held
            if held:
                assert "fields" not in record and "intro" not in record
                rows.append({"id": record["id"], "domain": "ditahan",
                             "state": record["state"], "flags": ["TAHAN_KANDUNGAN"]})
                continue
            assert record["state"] != "TAHAN_SEMAKAN_KANDUNGAN"
            fields = record["fields"]
            assert all(isinstance(fields.get(k), str) and fields[k].strip() for k in REQUIRED)
            assert "DRAF" in record["teacher_notice"]
            match = re.search(r"Bidang:\s*([^\s•]+)", " ".join(record.get("intro", [])))
            domain = DOMAINS.get(match.group(1), "tidak_diketahui") if match else "tidak_diketahui"
            steps = [s.strip() for s in fields["aktiviti_utama"].splitlines() if s.strip()]
            numbered = NUMBERED.match(steps[0])
            flags = []
            if not numbered or numbered.group(1) != "1":
                flags.append("NOMBOR_AKTIVITI_TIDAK_BERMULA_1")
            if len(steps) <= 2:
                flags.append("AKTIVITI_TERLALU_RINGKAS_PERLU_SEMAKAN")
            if any(term in fields["bahan"].casefold() for term in UNVERIFIED_PAGE):
                flags.append("RUJUKAN_HALAMAN_BELUM_DISAHKAN")
            source_toc = record.get("staging_textbook_toc_correction")
            if source_toc:
                assert year == 2 and record["id"] in ("T2-L102", "T2-L105", "T2-L108")
                assert source_toc["original_note_preserved"] is True
                assert source_toc["original_claimed_printed_pages"] == [133, 140]
                assert source_toc["proposed_section_range_for_editor"] == [133, 138]
                assert source_toc["sp_to_specific_page_verified"] is False
                assert source_toc["content_expert_approved"] is False
                assert source_toc["publication"] == "HOLD"
                assert "ms. 133–140" in fields["bahan"]
                flags.append("HALAMAN_BUKU_T2_MELEBIHI_MUKA_TERAKHIR")
            if GENERIC_PBD in fields["pentaksiran"]:
                flags.append("PBD_TIDAK_KHUSUS_KEPADA_SP")
            refinement = record.get("staging_pbd_refinement")
            if refinement:
                assert refinement.get("publication") == "HOLD"
                assert refinement.get("content_expert_approved") is False
                assert refinement.get("jawi_orthography_approved") is False
                assert refinement.get("word_pdf_tested") is False
                assert refinement.get("source_sk_sp_unchanged") is True
                assert refinement.get("book_or_verse_reference_added") is False
                assert GENERIC_PBD in refinement["original_pentaksiran"]
                assert GENERIC_PBD not in fields["pentaksiran"]
                specific = record.get("staging_dskp_l146_alignment")
                if specific:
                    assert record["id"] == "T3-L146" and year == 3
                    assert specific["original_pentaksiran"].startswith(
                        refinement["original_pentaksiran"].split("ڤبد اينديويدو:")[0])
                    assert refinement["assessment_criterion_review_only"] in specific["original_pentaksiran"]
                    assert refinement["observed_evidence_review_only"] in specific["original_pentaksiran"]
                    assert fields["pentaksiran"].startswith("ڤبد اينديويدو:")
                    assert "بخيل" not in fields["pentaksiran"]
                    assert "مروموس" in fields["pentaksiran"] and "ممڤراݢاكن" in fields["pentaksiran"]
                else:
                    assert fields["pentaksiran"].startswith(
                        refinement["original_pentaksiran"].split("ڤبد اينديويدو:")[0])
                    assert refinement["assessment_criterion_review_only"] in fields["pentaksiran"]
                    assert refinement["observed_evidence_review_only"] in fields["pentaksiran"]
                flags.append("PBD_SP_SASARAN_BELUM_DISAH_PAKAR")
            alignment = record.get("staging_dskp_l146_alignment")
            if alignment:
                assert year == 3 and record["id"] == "T3-L146"
                assert alignment["revision"] == "pi-year3-l146-dskp-6.4.3-6.4.5-20261107"
                assert alignment["dskp_pdf_page"] == 51
                assert alignment["dskp_printed_page"] == 39
                assert alignment["source_sp_codes"] == ["6.4.3","6.4.4","6.4.5"]
                assert alignment["source_sk_sp_unchanged"] is True
                assert alignment["original_objektif"].startswith("موريد داڤت")
                assert "2. مثنارايكن كڤنتيڠن" in alignment["original_objektif"]
                assert "2. مروموس كڤنتيڠن" in fields["objektif"]
                assert "3. مڠعملكن ساتو سنة رسول الله" in fields["objektif"]
                assert "2. " in alignment["original_aktiviti_utama"]
                assert "4. موريد ممڤراݢاكن" in fields["aktiviti_utama"]
                assert "بخيل" in alignment["original_pentaksiran"]
                assert alignment["content_expert_approved"] is False
                assert alignment["jawi_orthography_approved"] is False
                assert alignment["native_word_pdf_visual_approved"] is False
                assert alignment["publication"] == "HOLD"
                flags.append("DSKP_T3_L146_OBJECTIVE_PBD_REVISED_EXPERT_PENDING")
            # Script consistency is a QA task, never an automatic transliteration.
            if re.search(r"[A-Za-z]", fields["penutup"]):
                flags.append("PENUTUP_RUMI_SEMAK_PENYERAGAMAN_JAWI")
            if domain == "tidak_diketahui":
                flags.append("BIDANG_TIDAK_DIKENALI")
            enrichment = record.get("staging_enrichment")
            if enrichment:
                # A richer draft is NOT an approved/teacher-ready lesson.
                assert enrichment.get("content_expert_approved") is False
                assert enrichment.get("publication") == "HOLD"
                assert enrichment.get("source_sp_unchanged") is True
                assert isinstance(enrichment.get("original_activity"), str)
                assert enrichment["original_activity"].strip()
                flags.append("PENAMBAHAN_PDP_BELUM_SAH_PAKAR")
            hadith = record.get("staging_hadith_original_source_verified")
            if hadith:
                assert year == 4 and record["id"] == "T4-L083"
                assert record.get("staging_source_review_required") is True
                assert hadith["source_book_printed_page"] == 51
                assert hadith["source_dskp_printed_page"] == 27
                assert hadith["dskp_excerpt_ellipsis_preserved"] is True
                assert hadith["source_excerpt_not_full_hadith_narration"] is True
                assert hadith["source_excerpt_used"] in fields["sp"]
                assert hadith["original_fields_preserved"]["aktiviti_utama"].startswith("1. ")
                assert len(fields["aktiviti_utama"].splitlines()) >= 3
                assert hadith["expert_hadith_text_review_approved"] is False
                assert hadith["pedagogical_content_expert_approved"] is False
                assert hadith["jawi_orthography_approved"] is False
                assert hadith["publication"] == "HOLD"
                flags.append("HADIS_T4_PETIKAN_BUKU_DSKP_DRAF_SEMAK_PAKAR")
            tasmi = record.get("staging_tasmi_rpt_2027_review")
            if tasmi:
                assert year == 6 and record["id"] in ("T6-L137","T6-L141")
                assert record["staging_source_review_required"] is True
                assert tasmi["source_surah_list"] and len(tasmi["source_surah_list"]) == 4
                assert tasmi["original_source_sk_sp_unchanged"] is True
                assert tasmi["rpt_2027_has_exact_ayah_ranges_for_this_pdp"] is False
                assert tasmi["teacher_must_select_and_record_exact_ayah_ranges_before_pdp"] is True
                assert tasmi["no_three_level_dskp_sp_codes_assigned"] is True
                assert tasmi["original_fields_preserved"]["sk"] == fields["sk"]
                assert tasmi["original_fields_preserved"]["sp"] == fields["sp"]
                assert len(tasmi["original_fields_preserved"]["aktiviti_utama"].splitlines()) == 2
                assert len(fields["aktiviti_utama"].splitlines()) == 4
                assert tasmi["actual_ayah_range_verified"] is False
                assert tasmi["academic_expert_approved"] is False
                assert tasmi["jawi_orthography_approved"] is False
                assert tasmi["native_telegram_web_generator_verified"] is False
                assert tasmi["publication"] == "HOLD"
                flags.append("TASMI_T6_RPT_AYAT_BELUM_DITETAPKAN_GURU")
            if record.get("staging_source_review_required") is True:
                flags.append("SUMBER_KRITIKAL_BELUM_LENGKAP")
            rows.append({"id": record["id"], "domain": domain,
                         "state": record["state"], "flags": flags})
    assert len(rows) == 696
    flag_counts = Counter(flag for row in rows for flag in row["flags"])
    domain_counts = Counter(row["domain"] for row in rows)
    return {
        "subject": "Pendidikan Islam",
        "scope": "Tahun 2-6, staging only",
        "total": len(rows),
        "drafts": len(rows) - len(HELD),
        "held": len(HELD),
        "domain_counts": dict(sorted(domain_counts.items())),
        "flags": dict(sorted(flag_counts.items())),
        "quality_score_percent": None,
        "quality_80_certified": False,
        "expanded_activity_draft_count": flag_counts["PENAMBAHAN_PDP_BELUM_SAH_PAKAR"],
        "short_activity_count": flag_counts["AKTIVITI_TERLALU_RINGKAS_PERLU_SEMAKAN"],
        "critical_source_review_count": flag_counts["SUMBER_KRITIKAL_BELUM_LENGKAP"],
        "dskp_l146_alignment_editorial_review_count": flag_counts["DSKP_T3_L146_OBJECTIVE_PBD_REVISED_EXPERT_PENDING"],
        "t4_hadith_source_excerpt_editorial_review_count": flag_counts["HADIS_T4_PETIKAN_BUKU_DSKP_DRAF_SEMAK_PAKAR"],
        "t6_tasmi_rpt_editorial_range_review_count": flag_counts["TASMI_T6_RPT_AYAT_BELUM_DITETAPKAN_GURU"],
        "textbook_page_range_overrun_count": flag_counts["HALAMAN_BUKU_T2_MELEBIHI_MUKA_TERAKHIR"],
        "generic_pbd_count": flag_counts["PBD_TIDAK_KHUSUS_KEPADA_SP"],
        "refined_pbd_review_count": flag_counts["PBD_SP_SASARAN_BELUM_DISAH_PAKAR"],
        "closing_rumi_consistency_review_count": flag_counts["PENUTUP_RUMI_SEMAK_PENYERAGAMAN_JAWI"],
        "refined_pbd_review_by_year": {
            str(y): sum(1 for r in rows
                        if r["id"].startswith(f"T{y}-") and
                        "PBD_SP_SASARAN_BELUM_DISAH_PAKAR" in r["flags"])
            for y in COUNT
        },
        "generic_pbd_by_year": {
            str(y): sum(1 for r in rows
                        if r["id"].startswith(f"T{y}-") and
                        "PBD_TIDAK_KHUSUS_KEPADA_SP" in r["flags"])
            for y in COUNT
        },
        "mechanical_three_step_coverage_percent": round(
            100 * (690 - flag_counts["AKTIVITI_TERLALU_RINGKAS_PERLU_SEMAKAN"]) / 690, 2
        ),
        "academic_verification": "BELUM: DSKP, buku teks/mushaf, objektif, PBD & Jawi belum disahkan setiap Lesson",
        "format_revision": "560 DRAF diperkaya dengan langkah/PBD; cetakan draf 687/687 A4 satu halaman melalui LibreOffice (bukan penjana live); semakan visual Jawi dan kualiti akademik masih belum diluluskan",
        "release": "NO_GO",
        "records": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    result = audit()
    summary = {k: v for k, v in result.items() if k != "records"}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
