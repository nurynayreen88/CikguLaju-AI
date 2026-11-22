"""QA-only Word/PDF export of 52 KP2027 Bahasa Melayu SJK Year-1 drafts.

This is an isolated offline renderer, NOT a Web route, publication gate,
academic approval, live download, credit debit, or RPT calendar allocation.
Never import it from production Web or Telegram handlers.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "audits/kp2027_bm_sjk_tahun1_52_rph_editorial_qa_20261123.json"
PAGE_WIDTH_MM = 210
PAGE_HEIGHT_MM = 297
MARGIN_MM = 18
OUTER_WIDTH_MM = PAGE_WIDTH_MM - 2 * MARGIN_MM  # 174
LABEL_WIDTH_MM = 31
TONE = "EDF3FA"
STRONG = "DBE8F5"


def qa_records():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if data["status"] != "QA_HOLD_NOT_READY" or data["counts"] != {
        "sp": 26, "draft_rph": 52, "ready": 0
    }:
        raise ValueError("QA release gate unexpectedly changed")
    records = data["records"]
    if len(records) != 52 or [r["proposed_pdp"] for r in records] != list(range(1, 53)):
        raise ValueError("QA draft inventory changed")
    for r in records:
        if (r["status"] != "QA_HOLD_NOT_READY" or not r.get("sk_description")
                or not r.get("sp_description") or len(r["aktiviti_utama"]) != 3
                or r["refleksi_label"] != "Refleksi"):
            raise ValueError("A QA source is not complete for isolated export")
    return records


def heading(record):
    return (
        "RANCANGAN PENGAJARAN HARIAN",
        "BAHASA MELAYU (SJK) | TAHUN 1",
        f"PdP {record['proposed_pdp']:03d} | {record['title_editorial']}",
    )


def _rows(record):
    """One content model for both formats; do not rewrite source text."""
    standards = [
        ("Fokus", [record["focus_editorial"]]),
        ("Standard Kandungan", [record["sk_code"] + " " + record["sk_description"]]),
        ("Standard Pembelajaran", [record["sp_code"] + " " + record["sp_description"]] +
         record.get("sp_components", [])),
        ("Objektif Pembelajaran", record["objectives"]),
        ("Bahan Bantu Mengajar", record["bbm"]),
    ]
    activities = [("Set Induksi", [
        ("Guru", record["set_induksi"]["guru"]),
        ("Murid", record["set_induksi"]["murid"]),
    ])]
    for item in record["aktiviti_utama"]:
        activities.append((item["title"], [
            ("Guru", item["guru"]), ("Murid", item["murid"])
        ]))
    activities.append(("Penutup", [
        ("Guru", record["penutup"]["guru"]),
        ("Murid", record["penutup"]["murid"]),
    ]))
    follow_up = [
        ("Pentaksiran / PBD", [record["penilaian"]]),
        ("Pemulihan", [record["pemulihan"]]),
        ("Pengayaan", [record["pengayaan"]]),
        ("Refleksi", []),
    ]
    return standards, activities, follow_up


def render_docx(record):
    """Four equal-width outer tables, no template overlay or placeholders."""
    from docx import Document
    from docx.shared import Mm, Pt, RGBColor
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    d = Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Mm(PAGE_WIDTH_MM), Mm(PAGE_HEIGHT_MM)
    sec.left_margin = sec.right_margin = Mm(MARGIN_MM)
    sec.top_margin = sec.bottom_margin = Mm(16)

    normal = d.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(9)
    normal.font.color.rgb = RGBColor(25, 50, 73)
    normal.paragraph_format.space_after = Pt(2)

    def set_cell(cell, fill=None):
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        cell.margin_top = Mm(1)
        if fill:
            tc_pr = cell._tc.get_or_add_tcPr()
            shd = OxmlElement("w:shd")
            shd.set(qn("w:fill"), fill)
            tc_pr.append(shd)

    def put(cell, lines, *, bold_all=False):
        cell.text = ""
        p = cell.paragraphs[0]
        for i, (text, bold) in enumerate(lines):
            if i:
                p = cell.add_paragraph()
            run = p.add_run(str(text))
            run.bold = bold or bold_all
        return cell

    def table(widths, rows):
        t = d.add_table(rows=rows, cols=len(widths))
        t.autofit = False
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for c, width in zip(t.columns, widths):
            c.width = Mm(width)
        for row in t.rows:
            for cell, w in zip(row.cells, widths):
                cell.width = Mm(w)
                tc_pr = cell._tc.get_or_add_tcPr()
                borders = tc_pr.first_child_found_in("w:tcBorders")
                if borders is None:
                    borders = OxmlElement("w:tcBorders")
                    tc_pr.append(borders)
                for edge in ("top", "left", "bottom", "right"):
                    tag = qn("w:" + edge)
                    obj = borders.find(tag)
                    if obj is None:
                        obj = OxmlElement("w:" + edge)
                        borders.append(obj)
                    obj.set(qn("w:val"), "single")
                    obj.set(qn("w:sz"), "6")
                    obj.set(qn("w:color"), "8393A3")
                tr_pr = row._tr.get_or_add_trPr()
                cant_split = OxmlElement("w:cantSplit")
                tr_pr.append(cant_split)
        return t

    def spacer():
        d.add_paragraph().paragraph_format.space_after = Pt(1)

    h = heading(record)
    head = table((116, 58), 1)
    put(head.cell(0, 0), [(h[0], True), (h[1], True), (h[2], False)])
    set_cell(head.cell(0, 0), STRONG)
    put(head.cell(0, 1), [(s + ":", True) for s in ("Kelas", "Tarikh", "Masa", "Bil. Murid")])
    set_cell(head.cell(0, 1), TONE)
    spacer()
    standards, activities, follow_up = _rows(record)
    t = table((LABEL_WIDTH_MM, OUTER_WIDTH_MM-LABEL_WIDTH_MM), len(standards))
    for i, (label, contents) in enumerate(standards):
        put(t.cell(i, 0), [(label, True)])
        set_cell(t.cell(i, 0), TONE)
        put(t.cell(i, 1), [(x, False) for x in contents])
    spacer()
    t = table((LABEL_WIDTH_MM, OUTER_WIDTH_MM-LABEL_WIDTH_MM), len(activities))
    for i, (label, chunks) in enumerate(activities):
        put(t.cell(i, 0), [(label, True)])
        set_cell(t.cell(i, 0), TONE)
        put(t.cell(i, 1), [(role + ": " + value, False) for role, value in chunks])
    spacer()
    t = table((LABEL_WIDTH_MM, OUTER_WIDTH_MM-LABEL_WIDTH_MM), len(follow_up))
    for i, (label, contents) in enumerate(follow_up):
        put(t.cell(i, 0), [(label, True)])
        set_cell(t.cell(i, 0), TONE)
        put(t.cell(i, 1), [(x, False) for x in contents])
    # Reject accidentally added fifth table or text unrelated to source.
    if len(d.tables) != 4:
        raise AssertionError("Outer table contract failed")
    out = io.BytesIO()
    d.save(out)
    return out.getvalue()


def render_pdf(record):
    """Direct vector PDF using the same source, no redactions or overlays."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    font_dir = Path("/usr/share/fonts/truetype/dejavu")
    regular = font_dir / "DejaVuSans.ttf"
    bold = font_dir / "DejaVuSans-Bold.ttf"
    if not regular.exists() or not bold.exists():
        raise RuntimeError("DejaVu fonts needed for deterministic Malay PDF export")
    if "KPQA" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("KPQA", str(regular)))
        pdfmetrics.registerFont(TTFont("KPQABold", str(bold)))
        pdfmetrics.registerFontFamily("KPQA", normal="KPQA", bold="KPQABold")
    normal = ParagraphStyle(
        "KPQA", fontName="KPQA", fontSize=8.3, leading=12,
        alignment=TA_LEFT, textColor=colors.HexColor("#193249"), spaceAfter=1
    )
    def para(txt, bold=False):
        content = escape(str(txt))
        return Paragraph("<b>"+content+"</b>" if bold else content, normal)
    def pack(lines):
        if not lines:
            return para(" ")
        return [para(x) for x in lines]
    pdf = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf, pagesize=A4,
        leftMargin=MARGIN_MM*mm, rightMargin=MARGIN_MM*mm,
        topMargin=16*mm, bottomMargin=16*mm,
        title=f"RPH Bahasa Melayu SJK Tahun 1 PdP {record['proposed_pdp']:03d}"
    )
    width = OUTER_WIDTH_MM*mm
    def tb(rows, col_widths, shaded_rows):
        t = Table(rows, colWidths=[x*mm for x in col_widths], hAlign="LEFT")
        styles = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (-1, -1), .6, colors.HexColor("#8393A3")),
            ("INNERGRID", (0, 0), (-1, -1), .45, colors.HexColor("#8393A3")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
        for n in shaded_rows:
            styles.append(("BACKGROUND", (0, n), (0, n), colors.HexColor("#"+TONE)))
        t.setStyle(TableStyle(styles))
        if abs(sum(t._colWidths)-width) > 0.01:
            raise AssertionError("PDF table outer widths differ")
        return t

    h=heading(record)
    left = [para(x, bold=(i<2)) for i, x in enumerate(h)]
    right = [para(s+":") for s in ("Kelas", "Tarikh", "Masa", "Bil. Murid")]
    hdr = tb([[left, right]], [116, 58], [])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#"+STRONG)),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#"+TONE)),
    ]))
    story = [hdr, Spacer(1, 4*mm)]
    standards, activities, follow_up = _rows(record)
    def content_table(rows):
        return tb([[para(label, bold=True), pack(contents)] for label, contents in rows],
                  [LABEL_WIDTH_MM, OUTER_WIDTH_MM-LABEL_WIDTH_MM],
                  range(len(rows)))
    story += [content_table(standards), Spacer(1, 4*mm)]
    story += [content_table([
        (label, [role+": "+value for role, value in chunks])
        for label,chunks in activities
    ]), Spacer(1, 4*mm)]
    story.append(content_table(follow_up))
    doc.build(story)
    result=pdf.getvalue()
    if not result.startswith(b"%PDF-"):
        raise AssertionError("PDF source failed")
    return result


def export_all(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "release_gate": "QA_HOLD_NOT_READY", "ready": 0,
        "source": str(SOURCE.relative_to(ROOT)),
        "files": []
    }
    for r in qa_records():
        number=r["proposed_pdp"]
        for extension, render in (("docx",render_docx),("pdf",render_pdf)):
            name=f"CIKGULAJU_KP2027_BMSJK_T1_PDP{number:03d}_QA.{extension}"
            payload=render(r)
            (out_dir/name).write_bytes(payload)
            manifest["files"].append({
                "name": name,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "status": "QA_HOLD_NOT_READY",
            })
    assert len(manifest["files"]) == 104
    (out_dir/"manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return manifest


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args=ap.parse_args()
    m=export_all(args.out_dir)
    print("QA-only, not Web ready:",len(m["files"]),"Word/PDF files")
