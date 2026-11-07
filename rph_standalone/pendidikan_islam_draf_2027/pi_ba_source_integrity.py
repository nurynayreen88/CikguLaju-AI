"""Source-edition gate: mainstream KSSR Semakan is NOT special education KSSRPK.

Bibliographic metadata and public viewing URLs are evidence for source selection.
The gateway is intentionally NOT a copyright permission or textbook verification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED = {
    2: {
        "kpm_catalog_code": "BA102001",
        "school_subject_panel_viewer_page": "https://sites.google.com/moe-dl.edu.my/panitiapendidikanislamtldmkk/pembelajaran/tahun-2",
        "school_panel_lists_buku_aktiviti_title": True,
        "school_panel_proves_exact_printed_page": False,
        "kpm_catalog_url": "https://www.moe.gov.my/storage/files/shares/Banner/E-Katalog%20Buku%20Teks%20KPM.pdf",
        "publisher_from_kpm_catalog": "Dewan Bahasa dan Pustaka",
        "title_and_code_in_kpm_catalog_verified": True,
        "url": "https://anyflip.com/lhat/sebp/",
        "title": "Buku Aktiviti P. Islam Tahun 2 KSSR Semakan",
        "stream": "KSSR_SEMAKAN_ARUS_PERDANA",
        "source_verification": "PUBLIC_VIEWER_TITLE_AND_SCHOOL_PORTAL",
        "pdf_content_directly_inspected": False,
        "page_exercise_mapping_verified": False,
        "rights_to_redistribute": False
    },
    3: {
        "kpm_catalog_code": "BA103001",
        "school_subject_panel_viewer_page": "https://sites.google.com/moe-dl.edu.my/panitiapendidikanislamtldmkk/pembelajaran/tahun-3",
        "school_panel_lists_buku_aktiviti_title": True,
        "school_panel_proves_exact_printed_page": False,
        "kpm_catalog_url": "https://www.moe.gov.my/storage/files/shares/Banner/E-Katalog%20Buku%20Teks%20KPM.pdf",
        "publisher_from_kpm_catalog": "Dewan Bahasa dan Pustaka",
        "title_and_code_in_kpm_catalog_verified": True,
        "url": "https://anyflip.com/lhat/dkui/",
        "title": "Buku Aktiviti P. Islam Tahun 3 KSSR Semakan",
        "stream": "KSSR_SEMAKAN_ARUS_PERDANA",
        "source_verification": "PUBLIC_VIEWER_TITLE_AND_SCHOOL_PORTAL",
        "pdf_content_directly_inspected": False,
        "page_exercise_mapping_verified": False,
        "rights_to_redistribute": False
    }
}
# Caution: third-party pages often label the KSSRPK Year 2 book simply "BA PAI".
# The sample below has publisher year 2017 and ISBN 978-983-49-1622-0,
# and the corresponding textbook is explicitly titled 'Masalah Pembelajaran'.
BLOCKED = {
    "https://anyflip.com/iouzn/bnqr/basic": {
        "reason": "KSSRPK MASALAH PEMBELAJARAN, not mainstream KSSR",
        "book_isbn": "978-983-49-1622-0",
        "publisher_year": 2017,
        "evidence": "https://anyflip.com/nqvgv/fpob/basic"
    },
    "https://id.scribd.com/document/799936938/BA-PAI-TAHUN-2": {
        "reason": "Matched KSSRPK book by ISBN and contents, not mainstream KSSR",
        "book_isbn": "978-983-49-1622-0",
        "publisher_year": 2017,
        "evidence": "https://anyflip.com/nqvgv/fpob/basic"
    }
}


def normalized_url(url):
    return url.rstrip("/").split("?")[0]


def check_source(year, url):
    normalized = normalized_url(url)
    if normalized in BLOCKED:
        return {
            "allowed_for_review": False,
            "reason": BLOCKED[normalized]["reason"],
            "ready_for_teacher": False
        }
    expected = EXPECTED.get(year)
    if not expected or normalized != normalized_url(expected["url"]):
        return {
            "allowed_for_review": False,
            "reason": "Not the explicitly cross-listed year/stream viewer",
            "ready_for_teacher": False
        }
    return {
        "allowed_for_review": True,
        "reason": "Correct title/stream candidate only; no page or exercise verified",
        "ready_for_teacher": False
    }


def source_integrity_report():
    accepted = {str(y): {**src, **check_source(y, src["url"])} for y,src in EXPECTED.items()}
    rejected = [
        {"url":url, **meta, **check_source(2,url)}
        for url,meta in BLOCKED.items()
    ]
    assert len(accepted) == 2 and len(rejected) == 2
    assert accepted["2"]["kpm_catalog_code"] == "BA102001"
    assert accepted["3"]["kpm_catalog_code"] == "BA103001"
    assert all(x["allowed_for_review"] is True and
               x["ready_for_teacher"] is False for x in accepted.values())
    assert all(x["allowed_for_review"] is False for x in rejected)
    return {
        "subject": "Pendidikan Islam",
        "accepted_mainstream_viewer_candidates": accepted,
        "rejected_cross_curriculum_sources": rejected,
        "safe_for_pdf_distribution": False,
        "direct_page_verification_completed": False,
        "status": "STAGING_EDITION_GUARD_NO_GO"
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()
    r = source_integrity_report()
    Path(args.output).write_text(json.dumps(r, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in r.items() if k!="rejected_cross_curriculum_sources"},
                     ensure_ascii=False, indent=2))
