"""Secondary-source page hints. NOT verified book-page or exercise mappings.

Only teacher material with direct exercise-level evidence, SP match, edition checks,
and rights checks may graduate out of HOLD; this queue never changes RPH content.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import json

from pi_ba_match_queue import NEEDS_PAGE, match_queue

PDPR_2020 = "https://anyflip.com/rvse/yhcp/basic"
PDPR_2021 = "https://www.scribd.com/document/521518334/PENDIDIKAN-ISLAM-TAHUN-3"
VIDEO_JAWI_AWALAN = "https://www.youtube.com/watch?v=u-dmxZOf41g"
VIDEO_JAWI_APITAN = "https://www.youtube.com/watch?v=MSrVyaNELpo"
VIDEO_ADAB_T2 = "https://www.youtube.com/watch?v=75s3VFoIe40"

# id, suspected printed pages, required SP keyword, source, topic matched in
# secondary lesson plan / teacher guide / video DESCRIPTION.
# Not all pages shown by videos have been viewed or checked directly.
EVIDENCE = (
    ("T2-L108", (134,135,136), "رسول الله", VIDEO_ADAB_T2, "Kekasihku Rasulullah"),
    ("T3-L003", (65,66), "العليم", PDPR_2021, "Al-Alim dan Al-Hakim: pengertian dan dalil"),
    ("T3-L007", (67,68), "العليم", PDPR_2021, "Al-Alim dan Al-Hakim: kesan beriman"),
    ("T3-L004", (49,50,51), "اولن", VIDEO_JAWI_AWALAN, "Jawi imbuhan awalan"),
    ("T3-L008", (50,), "اولن", PDPR_2021, "Jawi awalan di/se/ke"),
    ("T3-L047", (120,121,122), "تيدور", PDPR_2021, "Adab tidur: kepentingan"),
    ("T3-L055", (85,86,87), "صلاة", PDPR_2021, "Solat sempurna: perkara membatalkan solat, cakupan halaman PdPR"),
    ("T3-L059", (85,86,87), "صلاة", PDPR_2021, "Solat sempurna: permasalahan membatalkan solat, cakupan halaman PdPR"),
    ("T3-L051", (85,86,87), "صلاة", PDPR_2021, "Perkara membatalkan solat"),
    ("T3-L053", (26,), "الفاتحة", PDPR_2021, "Pengenalan Surah Al-Fatihah"),
    ("T3-L057", (28,29,30), "الفاتحة", PDPR_2021, "Kefahaman Surah Al-Fatihah"),
    ("T3-L060", (54,55), "اخيرن", PDPR_2021, "Jawi imbuhan akhiran"),
    ("T3-L063", (106,107), "تبليغ", PDPR_2021, "Sirah sifat tabligh"),
    ("T3-L067", (106,107), "تبليغ", PDPR_2021, "Sirah sifat tabligh: keunggulan dan kepentingan"),
    ("T3-L068", (52,), "اخيرن", PDPR_2020, "Jawi menulis imbuhan akhiran"),
    ("T3-L075", (38,39), "حديث", PDPR_2021, "Yang muda dikasihi, yang tua dihormati"),
    ("T3-L079", (38,39), "حديث", PDPR_2021, "Yang muda dikasihi, yang tua dihormati: teks dan terjemahan"),
    ("T3-L084", (58,59,60), "اڤيتن", VIDEO_JAWI_APITAN, "Jawi negeri cantik budaya menarik"),
    ("T3-L087", (124,125), "علمو", PDPR_2020, "Menuntut ilmu: fardu ain dan fardu kifayah"),
    ("T3-L091", (124,125,126,127), "علمو", PDPR_2021, "Adab menuntut ilmu"),
    ("T3-L095", (126,), "علمو", PDPR_2020, "Kepentingan adab menuntut ilmu"),
    ("T3-L111", (90,91,92,93,94,95,96), "ابعاض", PDPR_2021, "Sunat Ab\'adh dan Hai\'at: julat latihan PdPR, bukan pilihan latihan tertentu"),
    ("T3-L114", (90,91,92,93,94,95,96), "ابعاض", PDPR_2021, "Sunat Ab\'adh dan Hai\'at: julat latihan PdPR, bukan pilihan latihan tertentu"),
    ("T3-L118", (90,91,92,93,94,95,96), "ابعاض", PDPR_2021, "Sunat Ab\'adh dan Hai\'at: julat latihan PdPR, bukan pilihan latihan tertentu"),
    ("T3-L128", (28,29,30), "الفاتحة", PDPR_2021, "Kefahaman Surah Al-Fatihah: makna dan pengajaran"),
    ("T3-L123", (59,), "اڤيتن", PDPR_2020, "Jawi imbuhan apitan: latihan menulis"),
    ("T3-L097", (35,), "إخفاء حقيقي", PDPR_2020, "Tajwid ikhfa hakiki"),
    ("T3-L099", (72,), "كتاب", PDPR_2020, "Beriman kepada kitab: pengertian dan dalil"),
    ("T3-L103", (73,), "كتاب", PDPR_2020, "Beriman kepada kitab: nama kitab"),
    ("T3-L119", (58,), "اڤيتن", PDPR_2020, "Menulis Jawi imbuhan apitan"),
)


def evidence_queue(root=None):
    a = match_queue(root=root)
    by_id = {r["id"]: r for r in a["rows"]}
    result = []
    seen = set()
    for id_, pages, marker, link, topic in EVIDENCE:
        assert id_ not in seen
        seen.add(id_)
        row = by_id[id_]
        assert row["disposition"] == NEEDS_PAGE, (id_, row["disposition"])
        assert marker in row["sp_original"], (id_, marker)
        assert all(1 <= p <= 250 for p in pages) and len(set(pages)) == len(pages)
        conflict = (id_ == "T3-L004")
        result.append({
            "lesson_id": id_,
            "year": row["year"],
            "sp_codes": row["sp_codes"],
            "sp_original": row["sp_original"],
            "topic_correspondence": topic,
            "secondary_source_url": link,
            "page_numbers_reported_by_secondary_source": list(pages),
            "cross_source_conflict_detected": conflict,
            "conflicting_source_url": PDPR_2021 if conflict else None,
            "conflict_note": (
                "PdPR 2021 menyenaraikan p65-66 untuk Jawi awalan walaupun "
                "p65-66 juga disenaraikan bagi topik Akidah dalam bahan sama; "
                "p49-51 hanyalah petunjuk daripada video guru, perlu semak buku asal."
                if conflict else None
            ),
            "page_number_is_verified_in_original_book": False,
            "actual_printed_book_seen_at_page": False,
            "exercise_instruction_verified": False,
            "edition_and_print_page_verified": False,
            "book_page_to_lesson_match_approved": False,
            "copyright_permission_to_distribute": False,
            "allow_auto_inject_to_rph": False,
            "source_credibility": "SECONDARY_TEACHER_RESOURCE_ONLY",
            "review_state": "SOURCE_PAGE_AWAITING_DIRECT_INSPECTION",
            "teacher_sentence": None,
            "review_next": "Inspect original book on reported printed page, verify exact exercise and "
                           "SP fit, obtain signoff and only then propose one concise RPH sentence.",
        })
    assert len(result) == 30
    return {
        "year2_year3_candidate_lessons": a["refined_page_review_candidates"],
        "secondary_page_hints": len(result),
        "hints_by_year": dict(Counter(r["year"] for r in result)),
        "page_mappings_verified_from_original": 0,
        "rph_activity_book_injections": 0,
        "status": "NO_GO_SECONDARY_EVIDENCE_ONLY",
        "rows": result
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()
    data = evidence_queue()
    Path(args.output).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k:v for k,v in data.items() if k!="rows"}, ensure_ascii=False, indent=2))
