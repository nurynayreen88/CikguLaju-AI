#!/usr/bin/env python3
"""Physically render all 270 Moral supplementary Word RPH to 5 PDFs.

A DOCX A4 section and 54 manual page breaks DO NOT prove 54 printed A4 pages.
This check uses actual LibreOffice conversion, inspects page count, A4
dimensions and each page's text. No RPH or live data is modified.
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rpt_2027.pendidikan_moral.complete_96_downloads import build_rph_docx


def audit_one(year: int, output: Path, soffice: str) -> None:
    docx = build_rph_docx(year, output / f"Moral_Tahun{year}_54_RPH_A4.docx")
    doc = Document(docx)
    section = doc.sections[0]
    assert abs(section.page_width.cm - 21.0) < 0.05
    assert abs(section.page_height.cm - 29.7) < 0.05
    heading_count = sum(p.text.startswith("RPH PENDIDIKAN MORAL TAHUN") for p in doc.paragraphs)
    assert heading_count == 54, (year, "missing Word RPH", heading_count)
    with TemporaryDirectory(prefix=f"moral_lo_{year}_") as temp:
        profile = Path(temp) / "profile"
        command = [soffice, f"-env:UserInstallation={profile.as_uri()}", "--headless",
                   "--convert-to", "pdf", "--outdir", str(output), str(docx)]
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=180)
        if result.returncode:
            raise AssertionError((year, "LibreOffice failed", result.stdout[-1000:], result.stderr[-1000:]))
    pdf = output / (docx.stem + ".pdf")
    assert pdf.is_file() and pdf.stat().st_size > 5000, (year, "PDF not rendered")
    reader = PdfReader(str(pdf))
    if len(reader.pages) != 54:
        print(f"FAIL Y{year}: 54 source RPH expanded to {len(reader.pages)} physical PDF pages")
        for idx, page in enumerate(reader.pages):
            t = " ".join((page.extract_text() or "").split()).upper()
            sessions = re.findall(r"RPH PENDIDIKAN MORAL TAHUN [2-6].{0,12}SESI [0-9]{3}", t)
            if not sessions:
                print(f"  physical page {idx+1}: no session heading (likely overflow)")
        raise AssertionError((year, "not one RPH per physical page", len(reader.pages)))
    from rpt_2027.pendidikan_moral.complete_96_downloads import source_rows
    numbers = [int(r["Sesi"]) for r in source_rows(year, "A") if r["Modul"] == "PENGUKUHAN"]
    assert len(numbers) == 54
    for idx, page in enumerate(reader.pages, 1):
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        assert abs(width - 595.28) < 1.0 and abs(height - 841.89) < 1.0, (year, idx, "non-A4")
        text = " ".join((page.extract_text() or "").split()).upper()
        # The 54 supplementary sessions are not numbered consecutively (core sessions interleave).
        # The authoritative source order comes from the same RPT used by the builder.
        expected = f"SESI {numbers[idx - 1]:03d}"
        if expected not in text:
            raise AssertionError((year, idx, "session heading absent or text spilled onto next page", expected))
        if text.count("RPH PENDIDIKAN MORAL TAHUN") != 1:
            raise AssertionError((year, idx, "missing or multiple RPH headings"))
        for label in ("OBJEKTIF", "AKTIVITI 1", "AKTIVITI 2", "PENUTUP"):
            if label not in text:
                raise AssertionError((year, idx, f"{label} missing from printed page"))
        if any(flag in text for flag in ("DRAF SEMAK", "BELUM READY", "BELUM_FINAL_READY")):
            raise AssertionError((year, idx, "internal audit label leaked"))
        if "**" in text or "`" in text:
            raise AssertionError((year, idx, "raw Markdown formatting leaked into printable RPH"))
    print(f"PASS YEAR{year}: 54/54 independent physical A4 Word-rendered RPH pages")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", required=True)
    p.add_argument("--soffice", default="libreoffice")
    args = p.parse_args()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    for year in range(2, 7):
        audit_one(year, outdir, args.soffice)
    print("PASS: 270/270 Moral supplementary RPH physically rendered onto one A4 page each.")
    print("Scope: Word print layout only; not source-text activity approval or real teacher Telegram delivery.")


if __name__ == "__main__":
    main()
