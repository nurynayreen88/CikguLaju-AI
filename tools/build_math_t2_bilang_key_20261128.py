"""Build only three teacher keys from the reviewed original pupil PDFs."""
import base64
import hashlib
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
import fitz

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "worksheets/staging/math_t2_004_005_011_qa_20261128.json"
OUT = ROOT / "math_t2_bilang_key_qa"
OUT.mkdir(exist_ok=True)
NAVY = HexColor("#243247")
GOLD = HexColor("#795a32")
PALE = HexColor("#f1ecdf")
SLATE = HexColor("#758195")
records = json.loads(SOURCE.read_text(encoding="utf-8"))["records"]
records = [r for r in records if r["title"] == "Bilang Nombor"]
assert len(records) == 1
for record in records:
    slug = record["title"].upper().replace(" ", "_")
    path = OUT / f"CIKGULAJU_MATEMATIK_T2_{slug}_SKEMA.pdf"
    c = canvas.Canvas(str(path), pagesize=A4, invariant=1, pageCompression=1)
    w, h = A4
    c.setTitle("CikguLaju - Skema Jawapan - " + record["title"])
    c.setFillColor(GOLD); c.rect(0, h-6, w, 6, fill=1, stroke=0)
    c.setFont("Helvetica-Bold",18); c.drawString(38,h-34,"CikguLaju")
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold",10)
    c.drawCentredString(w/2,h-29,"MATEMATIK SK - TAHUN 2")
    c.setFont("Helvetica",9); c.drawRightString(w-38,h-29,"SP "+record["sp"])
    c.setStrokeColor(SLATE); c.setLineWidth(.45); c.line(38,h-49,w-38,h-49)
    c.setFillColor(PALE); c.roundRect(38,h-82,w-76,23,5,fill=1,stroke=0)
    c.setFillColor(NAVY); c.setFont("Helvetica-Bold",10)
    c.drawString(49,h-74,"NOMBOR HINGGA 1 000")
    c.drawRightString(w-49,h-74,"SKEMA JAWAPAN")
    c.setFont("Helvetica-Bold",20); c.drawString(38,h-110,record["title"])
    c.setFont("Helvetica",10); c.drawString(38,h-129,"Panduan guru - jawapan bagi lembaran latihan asal")
    y=h-162
    expected=[]
    for section, lines in record["answer_key"]:
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold",12)
        c.drawString(38,y,"Bahagian "+section)
        expected.append("Bahagian "+section)
        y-=21
        c.setFillColor(NAVY); c.setFont("Helvetica",11)
        for line in lines:
            assert c.stringWidth(line,"Helvetica",11) < w-86
            c.drawString(47,y,line)
            expected.append(line)
            y-=19
        y-=12
    if record.get("teacher_note"):
        from reportlab.lib.utils import simpleSplit
        c.setFillColor(GOLD); c.setFont("Helvetica-Bold",10)
        c.drawString(38,y,"Catatan guru"); y-=17
        c.setFillColor(NAVY); c.setFont("Helvetica",10)
        for line in simpleSplit(record["teacher_note"],"Helvetica",10,w-76):
            c.drawString(38,y,line); y-=14
    assert y>55, (record["title"], y)
    c.setStrokeColor(SLATE); c.line(38,27,w-38,27)
    c.setFillColor(GOLD); c.setFont("Helvetica",8)
    c.drawString(38,14,"CIKGULAJU / SKEMA JAWAPAN")
    c.drawRightString(w-38,14,"1/1")
    c.showPage(); c.save()
    data=path.read_bytes()
    with fitz.open(path) as doc:
        assert len(doc)==1
        page=doc[0]
        assert abs(page.rect.width-595.28)<1 and abs(page.rect.height-841.89)<1
        text=page.get_text()
        for line in expected:
            assert line in text, line
        pix = page.get_pixmap(matrix=fitz.Matrix(1.2,1.2), alpha=False)
        pix.save(str(path.with_suffix(".png")))
        print("KEY_PREVIEW_JPEG",slug,base64.b64encode(pix.tobytes("jpeg", jpg_quality=75)).decode("ascii"))
    print("KEY_QA",slug,hashlib.sha256(data).hexdigest(),len(data))
    # Small generated, nonpersonal teacher answer keys only, for private asset handoff.
    print("KEY_B64",slug,base64.b64encode(data).decode("ascii"))
