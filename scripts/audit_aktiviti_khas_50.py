"""Render 50 draft RPH in Word and PDF and verify all are one A4 page.

Run in CI with LibreOffice (Word-to-PDF check); no DB, webhook or deploy access.
"""
from __future__ import annotations
import io
import shutil
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader
from rph_standalone.aktiviti_khas.engine import _catalog, render


TEACHER = {"class": "4 Anggerik", "date": "2026-11-06",
           "time": "08:00-09:00", "students": "32"}


def assert_a4_single_page(pdf_bytes, activity_id):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    if len(reader.pages) != 1:
        raise AssertionError(f"{activity_id}: expected 1 page, got {len(reader.pages)}")
    box = reader.pages[0].mediabox
    if abs(float(box.width) - 595.28) > 2 or abs(float(box.height) - 841.89) > 2:
        raise AssertionError(f"{activity_id}: not A4")
    return reader.pages[0].extract_text()


def main():
    source, _ = _catalog()
    rows = source["activities"]
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    if executable is None:
        raise SystemExit("LibreOffice required for Word visual/page-count audit")
    with tempfile.TemporaryDirectory(prefix="cikgulaju-special-rph-") as directory:
        work = Path(directory)
        docx_dir = work / "word"
        converted = work / "converted"
        docx_dir.mkdir()
        converted.mkdir()
        for row in rows:
            year = row["years"][0]
            content = render(row, year, TEACHER, "word")
            (docx_dir / (row["id"] + ".docx")).write_bytes(content)
            own_pdf = render(row, year, TEACHER, "pdf")
            text = assert_a4_single_page(own_pdf, row["id"])
            if row["title"] not in text:
                raise AssertionError(f"{row['id']}: missing PDF title")
        cmd = [executable, "-env:UserInstallation=" + (work / "profile").as_uri(),
               "--headless", "--convert-to", "pdf", "--outdir", str(converted)]
        cmd += [str(p) for p in sorted(docx_dir.glob("*.docx"))]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                encoding="utf-8", timeout=180, check=False)
        if result.returncode:
            raise AssertionError("LibreOffice render failed: " + result.stderr[:1000])
        pdfs = sorted(converted.glob("*.pdf"))
        if len(pdfs) != 50:
            raise AssertionError(f"Expected 50 Word-to-PDF conversions, got {len(pdfs)}")
        for pdf in pdfs:
            text = assert_a4_single_page(pdf.read_bytes(), pdf.stem)
            if "Aktiviti 1" not in text or "Aktiviti 2" not in text or "Aktiviti 3" not in text:
                raise AssertionError(f"{pdf.stem}: numbered activities lost")
    print("PASS: 50 original PDF and 50 Word-converted PDF are each one A4 page")


if __name__ == "__main__":
    main()
