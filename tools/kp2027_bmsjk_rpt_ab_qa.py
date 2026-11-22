"""Offline, non-publishable 2027 Group A/B RPT candidate review documents.

52 proposed PdP are NOT a complete annual teaching load. Dates are blank
because subject timetable, applicable holidays and minimum annual allocation
have not been provided/validated. No Web/Telegram imports, credit usage or
public endpoints.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "audits/kp2027_bm_sjk_rpt_2027_ab_calendar_unallocated_20261123.json"
SKSP = ROOT / "audits/kp2027_bm_sjk_sksp_verified_20261123.json"
TITLE = "RPT 2027 | Bahasa Melayu SJK Tahun 1 | Pemetaan 52 PdP"
WARNING = "Pemetaan cadangan sahaja. Belum RPT tahunan final; tarikh PdP kosong sehingga jadual waktu sekolah dan cuti disahkan."


def load_group(group):
    if group not in ("A","B"):
        raise ValueError("Invalid Group A/B")
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    verified = json.loads(SKSP.read_text(encoding="utf-8"))
    if (mapping["publishable"] or mapping["ready_rph"] != 0
            or mapping["status"] != "QA_HOLD_RPT_ANNUAL_NOT_COMPLETE"):
        raise ValueError("RPT QA release gate changed")
    config = mapping["groups"][group]
    rows = config["pdp_cadangan"]
    if len(rows)!=52 or [r["pdp_cadangan"] for r in rows]!=list(range(1,53)):
        raise ValueError("52 proposed rows missing")
    result=[]
    for r in rows:
        if r["tarikh"] is not None or r["masa"] is not None:
            raise ValueError("An unapproved date or time was added")
        sk,sp=r["sk"],r["sp"]
        if sk not in verified["sk"] or sp not in verified["sp"]:
            raise ValueError("Unverified DK standard")
        description=verified["sp"][sp]
        if sp=="1.2.2":
            description += " " + "; ".join(verified["special_sp_components"]["1.2.2"])
        result.append((f'{r["pdp_cadangan"]:03d}',r["fokus"],sk+" "+verified["sk"][sk],
                       sp+" "+description,r["fasa"].capitalize(),""))
    return config,result


def render_docx(group):
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.shared import Mm, Pt, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    cfg,rows=load_group(group)
    doc=Document()
    sec=doc.sections[0]
    sec.orientation=WD_ORIENT.LANDSCAPE
    sec.page_width=Mm(297)
    sec.page_height=Mm(210)
    sec.left_margin=sec.right_margin=Mm(12)
    sec.top_margin=sec.bottom_margin=Mm(13)
    normal=doc.styles["Normal"]
    normal.font.name="Arial"
    normal.font.size=Pt(8)
    normal.font.color.rgb=RGBColor(27,51,73)
    normal.paragraph_format.space_after=Pt(1)
    p=doc.add_paragraph(TITLE+" | Kumpulan "+group)
    p.style="Heading 1"
    p=doc.add_paragraph("Sesi: "+cfg["mula"]+" hingga "+cfg["akhir"]+
                        " | Bilangan PdP cadangan: 52 | Tarikh sebenar: belum ditetapkan")
    p=doc.add_paragraph(WARNING)
    p.runs[0].italic=True

    headers=("PdP","Bidang / Fokus","Standard Kandungan","Standard Pembelajaran",
             "Fasa","Tarikh")
    widths=(12,41,76,109,21,14)
    table=doc.add_table(rows=1,cols=6)
    table.style="Table Grid"
    table.autofit=False
    table.alignment=WD_TABLE_ALIGNMENT.CENTER
    for col,width in zip(table.columns,widths):
        col.width=Mm(width)
    for cell,title,width in zip(table.rows[0].cells,headers,widths):
        cell.width=Mm(width)
        cell.text=title
        for run in cell.paragraphs[0].runs:run.bold=True
    tr_pr=table.rows[0]._tr.get_or_add_trPr()
    marker=OxmlElement("w:tblHeader")
    marker.set(qn("w:val"),"true")
    tr_pr.append(marker)
    for index,row in enumerate(rows):
        cells=table.add_row().cells
        for cell,value,width in zip(cells,row,widths):
            cell.width=Mm(width)
            cell.text=value
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.TOP
        row_xml=table.rows[-1]._tr
        trp=row_xml.get_or_add_trPr()
        trp.append(OxmlElement("w:cantSplit"))
        if index%2==0:
            for cell in cells:
                shd=OxmlElement("w:shd")
                shd.set(qn("w:fill"),"F2F6FA")
                cell._tc.get_or_add_tcPr().append(shd)
    # No invented lesson dates. Explicitly note that actual annual allocation
    # remains subject to the school's weekly timetable and KPM requirements.
    doc.add_paragraph(
        "Semakan diperlukan: peruntukan masa BM SJK, jadual waktu, cuti perayaan/negeri, "+
        "aktiviti pengukuhan tahunan dan kelulusan pedagogi setiap PdP."
    )
    out=io.BytesIO()
    doc.save(out)
    return out.getvalue()


def render_pdf(group):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import landscape,A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle

    cfg, rows=load_group(group)
    fonts=Path("/usr/share/fonts/truetype/dejavu")
    if "KPRPT" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("KPRPT",str(fonts/"DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("KPRPTBold",str(fonts/"DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFontFamily("KPRPT",normal="KPRPT",bold="KPRPTBold")
    style=ParagraphStyle("NormalKPRPT",fontName="KPRPT",fontSize=7.2,leading=10,
                         alignment=TA_LEFT,textColor=colors.HexColor("#1B3349"))
    big=ParagraphStyle("HeaderKPRPT",parent=style,fontName="KPRPTBold",fontSize=12,leading=16)
    def para(value,bold=False):
        val=escape(str(value))
        return Paragraph("<b>"+val+"</b>" if bold else val,style)
    def footer(canvas,doc):
        canvas.saveState()
        canvas.setFont("KPRPT",7)
        canvas.drawRightString(285*mm,8*mm,"KP2027 | Pemetaan QA • Halaman "+str(doc.page))
        canvas.restoreState()
    out=io.BytesIO()
    doc=SimpleDocTemplate(out,pagesize=landscape(A4),
        leftMargin=12*mm,rightMargin=12*mm,topMargin=13*mm,bottomMargin=14*mm,
        title=TITLE+" Kumpulan "+group)
    story=[
        Paragraph(escape(TITLE+" | Kumpulan "+group),big),
        Spacer(1,3*mm),
        para("Sesi: "+cfg["mula"]+" hingga "+cfg["akhir"]+
             " | PdP cadangan: 52 | Tarikh PdP: belum ditetapkan"),
        Spacer(1,2*mm),
        para(WARNING),
        Spacer(1,3*mm),
    ]
    headers=("PdP","Bidang / Fokus","Standard Kandungan","Standard Pembelajaran",
             "Fasa","Tarikh")
    data=[[para(v,True) for v in headers]]
    data += [[para(v) for v in row] for row in rows]
    widths=[12*mm,41*mm,76*mm,109*mm,21*mm,14*mm]
    t=LongTable(data,colWidths=widths,repeatRows=1,hAlign="LEFT",
                splitByRow=1)
    st=[
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DBE8F5")),
        ("BOX",(0,0),(-1,-1),.6,colors.HexColor("#8393A3")),
        ("INNERGRID",(0,0),(-1,-1),.4,colors.HexColor("#8393A3")),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]
    for i in range(2,len(data),2):
        st.append(("BACKGROUND",(0,i),(-1,i),colors.HexColor("#F2F6FA")))
    t.setStyle(TableStyle(st))
    story.append(t)
    story += [Spacer(1,4*mm),para(
        "Baki semakan: peruntukan masa, jadual waktu sekolah, cuti negeri/perayaan, "+
        "pengukuhan tahunan serta kelulusan pedagogi."
    )]
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    payload=out.getvalue()
    if not payload.startswith(b"%PDF-"):
        raise AssertionError("RPT PDF failed")
    return payload


def export_all(folder):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    m={"status":"QA_HOLD_RPT_ANNUAL_NOT_COMPLETE","public":False,"files":[]}
    for group in ("A","B"):
        for ext,fn in (("docx",render_docx),("pdf",render_pdf)):
            name=f"CIKGULAJU_KP2027_RPT_BMSJK_T1_KUMPULAN_{group}_QA.{ext}"
            payload=fn(group)
            (folder/name).write_bytes(payload)
            m["files"].append({"name":name,"bytes":len(payload),
                "sha256":hashlib.sha256(payload).hexdigest()})
    (folder/"rpt_manifest.json").write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8")
    return m


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out-dir",required=True)
    m=export_all(parser.parse_args().out_dir)
    print("RPT candidate QA-only:",len(m["files"]),"files; not annual final.")
