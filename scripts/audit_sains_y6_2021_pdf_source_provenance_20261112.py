"""Read-only original-PDF provenance audit for 2021 BPK Sains Tahun 6.

Only records official SP code/page presence and a local file SHA256.
Does NOT retain or publish copyrighted DSKP statements, approve lesson mapping,
change teacher PDFs or write to a database. Any failed download is HOLD.
A local authorized PDF can be supplied with --pdf-path for offline verification.
"""
from __future__ import annotations

import argparse
from io import BytesIO
import hashlib
import json
from pathlib import Path
import re
import sys

import requests
from pypdf import PdfReader

from scripts.probe_sains_y6_2021_96_sp_anyflip_20261110 import (
    official_codes, CODE,
)

PDF_URLS = (
    "https://beebeeclassroom.com/wp-content/uploads/2022/04/"
    "DSKP-KSSR-Semakan-2017-Sains-Tahun-6_ISBN_.pdf",
)
MAX_PDF_BYTES = 20 * 1024 * 1024
MIN_PDF_BYTES = 100 * 1024
MIN_DSKP_PAGES = 90
MAX_DSKP_PAGES = 105
# The 2021 original has preliminary matter and ~40 printed pages preceding
# 42-74 where official Year6 SP tables are located. Never infer a code's
# provenance merely from a table of contents or a prose introduction.
FIRST_SP_PDF_INDEX = 45
HEADER_SP = re.compile(r"STANDARD\s+PEMBELAJARAN", re.I)
REQUIRED_MASTHEAD = ("SAINS", "TAHUN 6", "SEPTEMBER 2021", "KURIKULUM")


def normalize(s):
    return re.sub(r"\s+", " ", s or "").upper()


def pdf_code_page_audit(source: bytes, expected: set[str] | None = None):
    """Return non-reproducible index only; no DSKP body text exported."""
    expected = expected if expected is not None else official_codes()
    if (not isinstance(source, bytes) or not MIN_PDF_BYTES <= len(source) <= MAX_PDF_BYTES
            or not source.startswith(b"%PDF")):
        raise ValueError("Invalid PDF binary or out-of-bounds source size")
    if len(expected) != 96:
        raise ValueError("The independent expected 96-SP index is incomplete")
    pdf = PdfReader(BytesIO(source), strict=True)
    if pdf.is_encrypted:
        raise ValueError("Encrypted DSKP source")
    count = len(pdf.pages)
    if not MIN_DSKP_PAGES <= count <= MAX_DSKP_PAGES:
        raise ValueError("Unexpected DSKP page count; check edition/source")
    front = normalize(" ".join(pdf.pages[i].extract_text() or ""
                               for i in range(min(count, 7))))
    if not all(w in front for w in REQUIRED_MASTHEAD):
        raise ValueError("PDF masthead/2021 edition missing; source HOLD")

    code_pages = {}
    tables = 0
    for idx in range(FIRST_SP_PDF_INDEX, count):
        page_text = pdf.pages[idx].extract_text() or ""
        text = normalize(page_text)
        if not HEADER_SP.search(text):
            continue
        tables += 1
        for m in CODE.finditer(text):
            code = m.group(0)
            if code in expected:
                code_pages.setdefault(code, set()).add(idx + 1)
    missing = sorted(expected - code_pages.keys(), key=lambda s: tuple(map(int, s.split("."))))
    report = {
        "source_type": "ORIGINAL_EDITION_PDF_FACSIMILE",
        "source_pdf_sha256": hashlib.sha256(source).hexdigest(),
        "pdf_bytes": len(source),
        "pdf_pages": count,
        "year6_2021_masthead_seen": True,
        "sp_table_pages_with_extracted_text": tables,
        "expected_unique_sp": 96,
        "official_unique_code_hits": len(code_pages),
        "missing_codes": missing,
        "code_to_pdf_page_numbers": {
            key: sorted(value) for key, value in sorted(code_pages.items(),
                key=lambda kv: tuple(map(int, kv[0].split("."))))
        },
        "academic_release_approved": False,
        "source_visual_sp_text_signoff": False,
        "teacher_pdf_ready": False,
        "copyright_redistribution_permission_verified": False,
    }
    report["source_code_coverage_ready"] = pdf_coverage_complete(report)
    report["status"] = ("PDF_CODE_COVERAGE_FOUND_MANUAL_SOURCE_REVIEW_REQUIRED"
                        if report["source_code_coverage_ready"] else
                        "SOURCE_COVERAGE_BLOCKED")
    return report


def pdf_coverage_complete(r: dict):
    """Code-only prerequisite; never converts PDF/text to approved RPH."""
    return (isinstance(r, dict)
            and r.get("source_type") == "ORIGINAL_EDITION_PDF_FACSIMILE"
            and r.get("year6_2021_masthead_seen") is True
            and r.get("source_visual_sp_text_signoff") is False
            and r.get("academic_release_approved") is False
            and r.get("teacher_pdf_ready") is False
            and r.get("copyright_redistribution_permission_verified") is False
            and r.get("expected_unique_sp") == 96
            and r.get("official_unique_code_hits") == 96
            and isinstance(r.get("sp_table_pages_with_extracted_text"), int)
            and r["sp_table_pages_with_extracted_text"] >= 10
            and r.get("missing_codes") == []
            and isinstance(r.get("code_to_pdf_page_numbers"), dict)
            and set(r["code_to_pdf_page_numbers"]) == official_codes()
            and isinstance(r.get("source_pdf_sha256"), str)
            and len(r["source_pdf_sha256"]) == 64)


def download_pdf(url: str):
    result = requests.get(url, timeout=35,
                          headers={"User-Agent":"CikguLaju-RPT-internal-source-QA/1.0"},
                          stream=True)
    result.raise_for_status()
    chunks = []
    size = 0
    try:
        for chunk in result.iter_content(chunk_size=128*1024):
            size += len(chunk)
            if size > MAX_PDF_BYTES:
                raise ValueError("Downloaded PDF size exceeds read-only limit")
            chunks.append(chunk)
    finally:
        result.close()
    return b"".join(chunks)


def probe(local_pdf=None):
    source_list = [("authorized_local_pdf", Path(local_pdf).read_bytes())] if local_pdf else [
        (url, None) for url in PDF_URLS
    ]
    report = {"status":"SOURCE_COVERAGE_BLOCKED",
              "academic_release_approved":False,
              "teacher_pdf_ready":False,
              "pdf_sources": []}
    for url, pdf_bytes in source_list:
        record = {"source": url, "status": "SOURCE_COVERAGE_BLOCKED"}
        try:
            binary = pdf_bytes if pdf_bytes is not None else download_pdf(url)
            indexed = pdf_code_page_audit(binary)
            record.update(indexed)
        except Exception as exc:
            record["error"] = type(exc).__name__ + ": " + str(exc)[:300]
        print("SAINS_T6_2021_PDF_SOURCE", url, record.get("status"),
              record.get("official_unique_code_hits", 0),record.get("error",""),
              flush=True)
        report["pdf_sources"].append(record)
    if any(r.get("source_code_coverage_ready") is True for r in report["pdf_sources"]):
        report["status"] = "PDF_CODE_COVERAGE_FOUND_MANUAL_SOURCE_REVIEW_REQUIRED"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-path", type=Path,
                        help="Authorized local 2021 DSKP PDF; never committed or uploaded")
    parser.add_argument("--output", type=Path,
                        default=Path("output/sains_y6_2021_96_sp_pdf_provenance_20261112.json"))
    args = parser.parse_args(argv)
    result = probe(args.pdf_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n",
                           encoding="utf-8")
    if result["status"] == "SOURCE_COVERAGE_BLOCKED":
        raise SystemExit("BLOCKED: no 96-code DSKP 2021 PDF evidence; RPT must remain DRAFT")
    print("EVIDENCE ONLY: PDF code index complete; 96 SP text, lesson/source"
          " visual approval and copyright clearance remain HOLD", flush=True)


if __name__ == "__main__":
    main()
