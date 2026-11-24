"""Offline batch only: 178 Arabic Y4–6 draft RPH, native shared RTL grid.

Retains teaching text from original Markdown; SP statements are earlier
visual transcription candidates, not academic signoff. SK text remains
pending rather than invented. No changes to published routes or access.
"""
import csv
import hashlib
import json
import re
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from scripts.render_bahasa_arab_staging import fields, first, display_sk_sp
from web.arabic_rph_word import _table, _paragraph

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "rph_standalone/bahasa_arab"
BANK = ROOT / "audits/arabic_draft_y4_y6_sp_candidate_bank_20261124.json"
INDEX = ROOT / "rpt_2027/bahasa_arab/rpt_2027_KUMPULAN_A_INDEKS_PDP_DRAF.csv"
COUNTS = {4: 58, 5: 60, 6: 60}

def render(row, bank, dest):
    year, pdp = int(row["tahun"]), int(row["pdp"])
    path = SOURCE / f"year{year}/lesson_{pdp:03d}.md"
    raw = path.read_text(encoding="utf-8")
    _, f = fields(raw)
    assert display_sk_sp(first(f, "DSKP SK/SP", "Kod SK/SP", "SK/SP cadangan")) == f"{row['sk']} / {row['sp']}"
    statement = bank[str(year)]["entries"][row["sp"]]["text"]
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(1)
    sec.left_margin = sec.right_margin = Cm(1.15)
    title = doc.add_paragraph()
    _paragraph(title, "خطة التدريس اليومية لمادة اللغة العربية", bold=True, size=17, centered=True)
    title.paragraph_format.space_after = Pt(4)
    header = _table(doc, (9.95, 3.25, 5.5), [
        ("", "الفصل", ""), ("", "التاريخ", ""), ("", "الوقت", ""), ("", "عدد التلاميذ", "")
    ], align_right=True, teacher_left=True)
    cell = header.cell(0, 0).merge(header.cell(3, 0))
    for p in list(cell.paragraphs)[1:]:
        cell._tc.remove(p._p)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    shade = OxmlElement("w:shd")
    shade.set(qn("w:val"), "clear")
    shade.set(qn("w:fill"), "FCE8D8")
    cell._tc.get_or_add_tcPr().append(shade)
    numerals = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    identity = [("الصف", str(year).translate(numerals)), ("الوحدة", first(f, "Unit")), ("موضوع الدرس", first(f, "Fokus PdP", "Fokus"))]
    for i, (label, value) in enumerate(identity):
        assert value
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        p.paragraph_format.tab_stops.add_tab_stop(Cm(3.1))
        _paragraph(p, f"{label}:\t{value}", bold=i == 0, size=11)
    details = [
        ("معيار المحتوى", row["sk"]),
        ("معيار التعلّم", row["sp"] + " " + statement),
        ("هدف التعلّم", first(f, "Objektif PdP", "Objektif pembelajaran", "Objektif")),
        ("معيار النجاح", first(f, "Kriteria kejayaan")),
    ]
    vocabulary = first(f, "Kosa kata / ayat")
    if vocabulary:
        details.append(("المفردات", vocabulary))
    _table(doc, (4.3, 14.4), details)
    activities = [
        ("التمهيد", first(f, "Set induksi")),
        ("النشاط الأول", first(f, "Aktiviti 1")),
        ("النشاط الثاني", first(f, "Aktiviti 2")),
        ("التقويم التكويني", first(f, "Pengukuhan", "Penilaian (PBD)", "PBD")),
        ("الخاتمة", first(f, "Penutup")),
    ]
    _table(doc, (3.1, 12.0, 3.6), [("المرحلة", "أنشطة التعليم والتعلّم", "ملاحظات")] + [(k,v,"") for k,v in activities], header=True)
    footer = [
        ("الوسائل التعليمية", first(f, "BBM")),
        ("المرجع", row["halaman_buku"]),
        ("تأمّل المعلّم", first(f, "Refleksi guru", "Refleksi")),
    ]
    _table(doc, (4.3, 14.4), footer)
    # Native table helper uses 11 pt; compact mixed-language drafts to 9 pt
    # without changing words. Preserve header and all label emphasis.
    for table in doc.tables[1:]:
        for tr in table.rows:
            for c in tr.cells:
                for p in c.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(9)
                        rpr = run._r.get_or_add_rPr()
                        sz = rpr.find(qn("w:szCs"))
                        if sz is not None:
                            sz.set(qn("w:val"), "18")
    doc.core_properties.comments = "QA ONLY; SP transcription candidate; SK statement and academic approval pending."
    doc.save(dest)
    check = Document(dest)
    displayed = "\n".join(c.text for t in check.tables for r in t.rows for c in r.cells)
    assert len(check.tables) == 4
    assert all(abs(sum(c.width.mm for c in t.columns)-187)<1 for t in check.tables)
    assert all(v and v in displayed for _,v in identity + details + activities)
    assert footer[0][1] and footer[0][1] in displayed
    assert all(v in displayed for _,v in footer if v)
    assert all(not r.cells[2].text for r in check.tables[0].rows)
    return {"year":year, "pdp":pdp, "sk":row["sk"], "sp":row["sp"], "source_sha256":hashlib.sha256(raw.encode()).hexdigest(), "sp_candidate":True, "sk_description_pending":True, "ready":False}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    bank=json.loads(BANK.read_text(encoding="utf-8"))["years"]
    with INDEX.open(encoding="utf-8-sig",newline="") as f:
        rows=[r for r in csv.DictReader(f) if int(r["tahun"]) in COUNTS]
    assert len(rows)==178
    assert all(sum(int(r["tahun"])==y for r in rows)==n for y,n in COUNTS.items())
    results=[]
    for row in rows:
        dest=args.out / f"BA_T{row['tahun']}_{int(row['pdp']):03d}.docx"
        results.append(render(row,bank,dest))
    (args.out/"source-audit.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
    print("178/178 source draft Word candidates; academic approval remains pending")

if __name__=="__main__":
    main()
