#!/usr/bin/env python3
"""Build five BM 2027 landscape PDFs from the reviewed-in-staging RPT HTML.

These PDFs retain the DRAF notices and BELUM AGIH weeks. They do not change
curriculum source, school calendars, production databases or READY flags.
"""
from pathlib import Path
from html import escape
import json
import re
from weasyprint import HTML
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "rpt_2027" / "bahasa_melayu" / "keluaran_format_english"
DEST = ROOT / "rpt_2027" / "bahasa_melayu"
COUNTS = {2: 164, 3: 165, 4: 165, 5: 166, 6: 165}
CSS = """
@page {
  size: A4 landscape;
  margin: 11mm 10mm 14mm 10mm;
  @bottom-left {
    content: 'CIKGULAJU AI • BAHASA MELAYU 2027 • DRAF SEMAKAN';
    font-family: Arial, sans-serif;
    font-size: 7.5pt;
    color: #617287;
  }
  @bottom-right {
    content: 'Halaman ' counter(page) ' / ' counter(pages);
    font-family: Arial, sans-serif;
    font-size: 7.5pt;
    color: #617287;
  }
}
html, body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.week { break-inside: avoid; page-break-inside: avoid; }
tr { break-inside: avoid; page-break-inside: avoid; }
"""

def run():
    manifest = []
    for year, target_count in COUNTS.items():
        src = SRC / f"RPT_BM_TAHUN_{year}_2027_A_B_PER_LESSON_DRAF.html"
        doc = src.read_text(encoding="utf-8")
        row_ids = re.findall(r'<td class="id">PdP (\d{3})', doc)
        if [int(v) for v in row_ids] != list(range(1, target_count + 1)):
            raise AssertionError(f"Tahun {year}: expected {target_count} sequential PdP in HTML")
        if doc.count('class="weektitle"') != 44:
            raise AssertionError(f"Tahun {year}: HTML must contain 44 weeks")
        if "DRAF" not in doc or "BELUM AGIH" not in doc:
            raise AssertionError(f"Tahun {year}: draft/unscheduled disclosures missing")
        if re.search(r"\bLesson\b", doc):
            raise AssertionError(f"Tahun {year}: English label found in BM HTML")
        doc = doc.replace("</style>", CSS + "</style>", 1)
        output = DEST / f"RPT_Bahasa_Melayu_Tahun_{year}_2027_DRAF.pdf"
        HTML(string=doc, base_url=str(SRC)).write_pdf(str(output))
        raw = output.read_bytes()
        if not raw.startswith(b"%PDF-") or len(raw) < 50000:
            raise AssertionError(f"Tahun {year}: invalid PDF/too small")
        pdf = PdfReader(str(output))
        if not pdf.pages:
            raise AssertionError(f"Tahun {year}: no PDF pages")
        for i, page in enumerate(pdf.pages, start=1):
            if float(page.mediabox.width) <= float(page.mediabox.height):
                raise AssertionError(f"Tahun {year}: page {i} is not landscape")
        extracted = "\n".join(page.extract_text() or "" for page in pdf.pages)
        # PDF typography may insert line breaks between PdP and its number.
        pdf_ids = {int(v) for v in re.findall(r"\bPdP\s+(\d{3})\b", extracted)}
        missing = set(range(1, target_count + 1)) - pdf_ids
        if missing:
            raise AssertionError(f"Tahun {year}: missing PdP ids in PDF text: {sorted(missing)[:15]}")
        entry = {"year": year, "pdp": target_count, "weeks": 44,
                 "pages": len(pdf.pages), "bytes": len(raw),
                 "landscape": True, "extracted_pdp": len(pdf_ids),
                 "status": "DRAF_BELUM_READY", "filename": output.name}
        manifest.append(entry)
        print(json.dumps(entry, ensure_ascii=False), flush=True)
    (DEST / "PDF_DRAF_MANIFEST_2027.json").write_text(
        json.dumps({"subject": "Bahasa Melayu SK", "year": 2027,
                    "ready": False, "records": manifest}, indent=2, ensure_ascii=False)+"\n",
        encoding="utf-8")
    assert sum(v["pdp"] for v in manifest) == 825

if __name__ == "__main__":
    run()
