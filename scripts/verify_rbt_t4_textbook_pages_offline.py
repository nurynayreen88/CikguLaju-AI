"""Verify Year 4 RBT textbook printed-page references against original PDF.

Run locally against the user's Drive source PDF. Do not upload 124 MB textbook
to GitHub or treat code presence as activity/visual/pedagogical approval.

Usage: python scripts/verify_rbt_t4_textbook_pages_offline.py \
       --pdf /path/to/GuruBesar_BukuTeks_RBT_T4_SK.pdf \
       --out /tmp/rbt_t4_page_proof.json
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "audits/rbt_t4_textbook_sp_page_map_20261106.json"


def verify(pdf_path: Path) -> dict:
    import fitz

    evidence = json.loads(SOURCE.read_text(encoding="utf-8"))
    code_pages = evidence["sp_printed_page_index"]
    offset = evidence["textbook"]["physical_pdf_page_offset"]
    if (len(code_pages) != 57 or evidence["mapped_sp_codes"] != 57
            or offset != 6 or evidence["visual_lesson_approvals"] != 0):
        raise ValueError("RBT T4 source ledger changed; manual review required")
    digest = hashlib.sha256()
    with pdf_path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    doc = fitz.open(pdf_path)
    if doc.page_count != 104:
        raise ValueError("Unexpected RBT Year 4 book PDF edition/page count")
    rows = []
    for code, pages in code_pages.items():
        proofs = []
        if not re.fullmatch(r"\d+\.\d+\.\d+", code) or not pages:
            raise ValueError(f"Invalid source code/page list: {code}")
        for printed in pages:
            index = int(printed) + offset - 1
            if not 0 <= index < doc.page_count:
                raise ValueError(f"Invalid PDF page for {code}: {printed}")
            txt = doc[index].get_text()
            found = bool(re.search(r"(?<![\d.])" + re.escape(code) + r"(?![\d.])", txt))
            proofs.append({
                "printed_page": int(printed),
                "pdf_page_1based": index + 1,
                "code_present": found
            })
        rows.append({
            "sp_code": code,
            "all_listed_pages_contain_code": all(x["code_present"] for x in proofs),
            "printed_pages": proofs
        })
    found = sum(int(r["all_listed_pages_contain_code"]) for r in rows)
    report = {
        "audit_date": date.today().isoformat(),
        "subject": "RBT",
        "year": 4,
        "source_title": evidence["textbook"]["title"],
        "source_drive_url": evidence["textbook"]["source"],
        "source_pdf_sha256": digest.hexdigest(),
        "source_pdf_pages": doc.page_count,
        "ledger_path": str(SOURCE.relative_to(ROOT)),
        "verification_kind": "TEXTUAL_SP_CODE_ON_EXACT_PRINTED_BOOK_PAGE",
        "verification_excludes": [
            "activity_visual_approval", "picture_correctness",
            "teacher_signoff", "project_safety_signoff",
            "printed_page_is_correct_for_full_learning_activity"
        ],
        "standards_checked": len(rows),
        "standards_with_matching_codes": found,
        "individual_page_checks": sum(len(row["printed_pages"]) for row in rows),
        "all_checks_passed": found == len(rows),
        "records": rows,
    }
    if not report["all_checks_passed"]:
        raise ValueError("One or more ledger page references do not contain their SP code")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = verify(args.pdf)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"RBT Tahun 4: {report['standards_with_matching_codes']}/57 SP, "
          f"{report['individual_page_checks']} indexed printed-page checks PASSED")
    print(f"Evidence hash: {report['source_pdf_sha256']}")


if __name__ == "__main__":
    main()
