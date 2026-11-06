"""Create internal DRAF Word/PDF RPT previews; no public runtime registration."""
import csv
import os
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MUSIC_RPT_DRAFT_DIR", "/tmp/muzik-rpt-2027-draf"))


ALIASES = {
    "slot_a": ("Slot A", "Slot Kumpulan A", "Kumpulan A slot 2027"),
    "slot_b": ("Slot B", "Slot Kumpulan B", "Kumpulan B slot 2027"),
    "unit": ("Unit", "Unit/Tajuk"),
    "sp": ("SP DSKP", "Kod SP", "SP"),
    "book": ("BT m/s", "Buku Teks m/s", "RPT halaman BT (belum sah)"),
    "status": ("Semakan", "Status Semakan", "Status tambahan"),
}


def pick(row, key):
    for field in ALIASES[key]:
        if field in row:
            return row[field]
    raise ValueError(f"Missing RPT column for {key}: {sorted(row)}")


def make_rpt(year: int) -> tuple[Path, Path]:
    path = ROOT / f"year{year}" / f"RPT_MUZIK_TAHUN_{year}_2027_DRAF.csv"
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 35, f"Year {year} missing PdP"
    assert [r["PdP ID"] for r in rows] == [f"MZ-Y{year}-{i:02d}" for i in range(1, 36)]
    assert all(pick(r, "slot_a") and pick(r, "slot_b") and pick(r, "sp") and pick(r, "unit") for r in rows)
    for number in (6, 19):
        assert "PDP ANJAL" in pick(rows[number - 1], "status")

    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(29.7), Cm(21)
    section.top_margin = section.bottom_margin = Cm(1.2)
    section.left_margin = section.right_margin = Cm(1.25)
    styles = doc.styles
    styles["Normal"].font.name = "Aptos"
    styles["Normal"].font.size = Pt(9)

    doc.add_paragraph("\n\n")
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("CIKGULAJU\nRANCANGAN PENGAJARAN TAHUNAN")
    run.bold = True
    run.font.size = Pt(25)
    year_line = doc.add_paragraph(f"PENDIDIKAN MUZIK TAHUN {year}  |  2027")
    year_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    year_line.runs[0].font.size = Pt(18)
    for line in ("KUMPULAN A & KUMPULAN B", "Sekolah: ______________________________",
                 "Nama guru: ____________________________", "Status: DRAF STAGING - BUKAN UNTUK EDARAN"):
        paragraph = doc.add_paragraph(line)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

    doc.add_heading(f"RPT PENDIDIKAN MUZIK TAHUN {year} - 2027", level=1)
    doc.add_paragraph(
        "Slot A/B ialah julat cadangan RPT, bukan tarikh PdP kelas yang telah disahkan. "
        "PdP 06 dan 19 perlu anjal berdasarkan negeri dan jadual guru. "
        "Semakan buku yang dicatat ialah semakan teks terhad; tiada fail audio yang disahkan."
    )
    table = doc.add_table(rows=1, cols=6)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = [Cm(1.2), Cm(2.6), Cm(2.6), Cm(9.4), Cm(7.8), Cm(2.7)]
    heads = ["PdP", "Kumpulan A", "Kumpulan B", "Unit / Tajuk", "SK / SP", "Buku m/s"]
    for col, (name, width) in enumerate(zip(heads, widths)):
        table.columns[col].width = width
        table.rows[0].cells[col].text = name
    for idx, row in enumerate(rows, start=1):
        cells = table.add_row().cells
        sp_codes = [p.strip() for p in pick(row, "sp").split(";") if p.strip()]
        sk_codes = list(dict.fromkeys(("3.1" if code.startswith("3.2.") else "4.1" if code == "4.2.1" else ".".join(code.split(".")[:2])) if year == 4 else ".".join(code.split(".")[:2]) for code in sp_codes))
        values = [
            f"{idx:02d}", pick(row, "slot_a"), pick(row, "slot_b"),
            pick(row, "unit") + ("  [ANJAL]" if idx in (6, 19) else ""),
            "SK: " + ", ".join(sk_codes) + "\nSP: " + ", ".join(sp_codes),
            pick(row, "book") or "-",
        ]
        for i, value in enumerate(values):
            cells[i].text = value
    # Repeating table headers and uniform small text for multipage RPT.
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    trpr = table.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    trpr.append(repeat)
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            cell.width = widths[i]
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(8)
    doc.add_paragraph(
        "Nota penerbitan: Dokumen ini semakan dalaman, bukan RPT FINAL READY. "
        "Kod SP Tahun 4 PdP21/24 mengikut cetakan DSKP/buku; "
        "perbezaan SK 3.1 dan SP 3.2.x masih memerlukan pengesahan."
    )
    docx = OUT / f"RPT_MUZIK_TAHUN_{year}_2027_DRAF.docx"
    doc.save(docx)
    back = Document(docx)
    assert len(back.tables) == 1 and len(back.tables[0].rows) == 36

    command = [
        "libreoffice", "-env:UserInstallation=file:///tmp/muzik_rpt_lo_profile",
        "--headless", "--convert-to", "pdf", "--outdir", str(OUT), str(docx)
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    pdf = docx.with_suffix(".pdf")
    assert pdf.exists() and len(PdfReader(str(pdf)).pages) >= 2
    return docx, pdf


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for current_year in range(2, 7):
        word, pdf = make_rpt(current_year)
        print(f"PASS staging RPT T{current_year}: {word.name} / {pdf.name}")
