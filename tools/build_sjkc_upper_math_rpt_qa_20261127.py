"""Isolated draft renderer. Never writes into rpt_2027 or live routes."""
import argparse
import json
from pathlib import Path
import subprocess
from datetime import date
from collections import Counter
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
import fitz

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "audits/rpt_2027_matematik_sjkc_t4_t6_layout_input_20261127.json"
FONT = "Noto Sans CJK SC"
HEADERS = ("周次 / Minggu", "教学编号", "单元 / Unit", "内容标准\nSK（编号）", "学习标准\nSP（编号）", "教学重点（草案）", "课本页码（待核）", "分钟")
WIDTHS = (3.4, 1.7, 3.4, 2.1, 2.4, 9.1, 2.5, 1.4)

def style_run(run, size=10, bold=False, color=None):
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)

def paragraph(container, text, size=10, bold=False, align=None, color=None):
    p = container.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    if align is not None:
        p.alignment = align
    style_run(p.add_run(text), size, bold, color)
    return p

def cell_text(cell, text, *, header=False, center=False, keep=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_with_next = keep
    p.paragraph_format.keep_together = True
    if center or header:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(p.add_run(text), 9 if header else 9.5, header, "FFFFFF" if header else "182B39")
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    if header:
        sh = OxmlElement("w:shd")
        sh.set(qn("w:fill"), "214E65")
        cell._tc.get_or_add_tcPr().append(sh)

def set_row(row, header=False):
    pr = row._tr.get_or_add_trPr()
    pr.append(OxmlElement("w:cantSplit"))
    if header:
        pr.append(OxmlElement("w:tblHeader"))

def span(group):
    return date.fromisoformat(group["start"]).strftime("%d/%m") + "–" + date.fromisoformat(group["end"]).strftime("%d/%m")

def build(plan, out):
    year = plan["year"]
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Cm(29.7), Cm(21)
    section.left_margin = section.right_margin = Cm(1.5)
    section.top_margin = section.bottom_margin = Cm(1.5)
    section.header_distance = section.footer_distance = Cm(.6)
    section.different_first_page_header_footer = True
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(10)
    style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    hp = section.header.paragraphs[0]
    style_run(hp.add_run(f"CikguLaju | RPT 2027 | 数学 · {year} 年级 | DRAF SEMAKAN"), 9, True, "214E65")
    fp = section.footer.paragraphs[0]
    style_run(fp.add_run("DRAF — BELUM UNTUK PENERBITAN  ·  "), 8, False, "805523")
    fld = OxmlElement("w:fldSimple"); fld.set(qn("w:instr"), "PAGE")
    fp._p.append(fld)
    center = WD_ALIGN_PARAGRAPH.CENTER
    paragraph(doc, "CIKGULAJU", 18, True, center, "214E65")
    paragraph(doc, "RANCANGAN PENGAJARAN TAHUNAN 2027", 25, True, center, "214E65")
    paragraph(doc, f"全年教学计划 · 数学 · {year} 年级", 22, True, center)
    paragraph(doc, f"MATEMATIK SJKC TAHUN {year} | KUMPULAN A & B", 13, True, center)
    paragraph(doc, "DRAF SEMAKAN · 仅供审核", 15, True, center, "805523")
    paragraph(doc, "Lencana sekolah: belum dipadankan", 11, False, center)
    paragraph(doc, "Nama sekolah / 学校：", 11, False, center)
    paragraph(doc, "Nama guru / 教师：", 11, False, center)
    paragraph(doc, "96 jam PdP + 5 jam pengukuhan (cadangan)", 11, False, center)
    paragraph(doc, "SK/SP penuh, halaman buku teks dan padanan RPH belum disahkan. Bukan dokumen produksi.", 10, False, center)
    doc.add_page_break()
    paragraph(doc, f"数学 {year} 年级 | RPT 2027", 15, True, color="214E65")
    paragraph(doc, "课本页码仅供核对；教学标准全文待确认。A/B tarikh draf, bukan pengesahan cuti negeri.", 9)
    table = doc.add_table(rows=1, cols=len(HEADERS))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for col, width in zip(table.columns, WIDTHS):
        col.width = Cm(width)
    for c, width, h in zip(table.rows[0].cells, WIDTHS, HEADERS):
        c.width = Cm(width)
        cell_text(c, h, header=True)
    set_row(table.rows[0], True)
    for week in plan["weeks"]:
        start = len(table.rows)
        for i, item in enumerate(week["rows"]):
            row = table.add_row()
            set_row(row)
            is_last = i == len(week["rows"])-1
            number = f'{item["draft_pdp"]:03d}' if item["kind"] == "instruction" else "—"
            pages = item.get("textbook_candidate_pages")
            page_text = (f"{pages[0]}–{pages[1]}*" if pages[0] != pages[1] else f"{pages[0]}*") if pages else "待核"
            values = (
                week["week"] + "\nA " + span(week["A"]) + "\nB " + span(week["B"]) if i == 0 else "",
                number, str(item["unit"])+" "+plan["unit_titles"][item["unit"]-1],
                "\n".join(item.get("sk_codes", [])) or "—",
                "\n".join(item.get("sp_codes", [])) or "—",
                item["topic"], page_text if item["kind"]=="instruction" else "—", str(item["minutes"])
            )
            for j, (c, width, v) in enumerate(zip(row.cells, WIDTHS, values)):
                c.width = Cm(width)
                cell_text(c, v, center=j in (0,1,3,4,6,7), keep=not is_last)
        end = len(table.rows)-1
        if start != end:
            merged = table.cell(start, 0).merge(table.cell(end, 0))
            cell_text(merged, week["week"]+"\nA "+span(week["A"])+"\nB "+span(week["B"]), center=True, keep=True)
    doc.add_page_break()
    paragraph(doc, "Rujukan dan status semakan / 参考资料与审核状态", 16, True, color="214E65")
    paragraph(doc, "DSKP: "+plan["source_dskp"], 9)
    paragraph(doc, "Buku teks: "+plan["source_textbook"], 9)
    paragraph(doc, "Agihan sementara berdasarkan data induk CikguLaju; 35 minggu, 96 sesi pengajaran dan lima sesi pengukuhan tanpa nombor RPH.", 10)
    paragraph(doc, "* Halaman cadangan belum disahkan pada setiap PdP. Tahun 5 tidak mempunyai nombor halaman buku teks yang disahkan.", 10)
    paragraph(doc, "Senarai cuti dan pengecualian kumpulan A/B perlu disahkan sebelum penerbitan. SK/SP dipaparkan sebagai kod sahaja; pernyataan penuh belum tersedia.", 10)
    doc.core_properties.title = f"DRAF RPT Matematik SJKC Tahun {year} 2027"
    doc.core_properties.author = "CikguLaju"
    target = out / f"DRAF_QA_RPT_Matematik_SJKC_Tahun_{year}_2027.docx"
    doc.save(target)
    check = Document(target)
    assert len(check.tables) == 1 and len(check.tables[0].rows) == 102
    assert check.tables[0].rows[0]._tr.xpath(".//w:tblHeader")
    subprocess.run(["libreoffice", "-env:UserInstallation=file:///tmp/sjkc-math-rpt-qa-profile", "--headless", "--convert-to", "pdf", "--outdir", str(out), str(target)], check=True)
    pdf_path = target.with_suffix(".pdf")
    assert pdf_path.is_file()
    with fitz.open(pdf_path) as pdf:
        assert len(pdf) >= 4
        for page in pdf:
            assert abs(page.rect.width-841.89) < 5 and abs(page.rect.height-595.28) < 5
        texts = [page.get_text() for page in pdf]
        # Each teaching page must retain the real table header.
        assert all("教学编号" in t and "SP（编号）" in t.replace(" ", "").replace("\n", "") for t in texts[1:-1]), "missing table header"
        # Check all teaching IDs by exact text line, including split across pages.
        counts = Counter(line.strip() for t in texts[1:-1] for line in t.splitlines())
        assert all(counts[f"{n:03d}"]==1 for n in range(1,97)), "missing/duplicate teaching IDs"
        for i,page in enumerate(pdf):
            page.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(out / f"QA_Y{year}_page_{i+1:02d}.png")
        return {"year":year,"pages":len(pdf),"rows":101,"release":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    out=args.out.resolve()
    assert not out.is_relative_to(ROOT/"rpt_2027"), "production folder forbidden"
    out.mkdir(parents=True, exist_ok=True)
    data=json.loads(SOURCE.read_text())
    assert data["status"]=="LAYOUT_QA_INPUT_ONLY_NOT_RELEASED"
    results=[build(p,out) for p in data["plans"]]
    (out/"qa_manifest.json").write_text(json.dumps({"status":"RENDERED_PENDING_VISUAL_ACADEMIC_QA","plans":results},indent=2))
    print(results)

if __name__=="__main__":
    main()
