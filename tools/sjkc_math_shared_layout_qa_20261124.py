"""QA-only shared layout for reviewed SJKC Mathematics Year 2/3 Word sources.

The current renderer remains untouched until source parity, PDF and visual QA pass.
No new curriculum text is synthesized. The input must be one resolved lesson.
"""
from io import BytesIO
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, Twips

FONT = "Noto Sans CJK SC"
TONE = "EDF0FB"
HEADER = "DFE4F8"
WIDTH = 182
LABEL_WIDTH = 47
MINUTES = re.compile(r"\s*\d{1,2}\s*分钟\s*$")


def _xml(parent, tag, **attrs):
    element = OxmlElement("w:" + tag)
    for key, value in attrs.items():
        element.set(qn("w:" + key), str(value))
    parent.append(element)
    return element


def _run(p, text, bold=False, size=9):
    r = p.add_run(text)
    r.bold = bold
    r.font.name = FONT
    r.font.size = Pt(size)
    r._r.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    return r


def _fill(cell, color):
    _xml(cell._tc.get_or_add_tcPr(), "shd", fill=color, val="clear")


def _table(doc, left, right):
    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for col, width in zip(t.columns, (Mm(left).twips, Mm(WIDTH).twips-Mm(left).twips)):
        col.width = Twips(width)
    pr = t._tbl.tblPr
    tw = pr.find(qn("w:tblW"))
    tw.set(qn("w:type"), "dxa")
    tw.set(qn("w:w"), str(Mm(WIDTH).twips))
    borders = _xml(pr, "tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        _xml(borders, edge, val="single", sz=4, color="8792A3")
    margins = _xml(pr, "tblCellMar")
    for edge in ("top", "bottom", "left", "right"):
        _xml(margins, edge, w=65, type="dxa")
    return t


def _row(t, left, right):
    row = t.add_row()
    for i, w in enumerate((Mm(left).twips, Mm(WIDTH).twips-Mm(left).twips)):
        row.cells[i].width = Twips(w)
        row.cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    return row.cells


def _line(cell, text, bold=False, first=False, size=9):
    p = cell.paragraphs[0] if first else cell.add_paragraph()
    _run(p, text, bold, size)
    return p


def _value(t, label, value):
    a, b = _row(t, LABEL_WIDTH, WIDTH-LABEL_WIDTH)
    _fill(a, TONE)
    _line(a, label, True, True)
    if value:
        _line(b, value, first=True)
    return b


def _extract_year2(source, lesson, ps):
    # Exact structure of staging/matematik_sjkc/tahun_2/build_word.py.
    # Rows without a header: standards/references, objective, induction,
    # two main activities, PBD activity, closure and materials (7 total).
    if (len(ps) != 5 or not re.match(r"^PdP\\s+%03d\\b" % lesson["pdp"], ps[0])
            or ps[1] != lesson["topic"]
            or not ps[2].startswith("Unit " + str(lesson["unit_number"]) + " ")
            or not ps[3].startswith("日期 Tarikh ")
            or ps[4] != "教学反思  Refleksi"):
        raise ValueError("Unexpected Year 2 source header")
    if len(source.tables) != 1:
        raise ValueError("Unexpected Year 2 table count")
    table = source.tables[0]
    if (len(table.rows), len(table.columns)) != (7, 2):
        raise ValueError("Unexpected Year 2 source table")
    labels = [MINUTES.sub("", r.cells[0].text).strip() for r in table.rows]
    expected = ["课程标准及参考", "学习目标", "导入", "主要教学活动",
                "巩固与课堂评估", "总结", "教具"]
    if labels != expected:
        raise ValueError("Unexpected Year 2 row labels: " + repr(labels))
    refs = [p.text for p in table.cell(0,1).paragraphs]
    if len(refs) != 2 or not refs[0].startswith("SK ") or not refs[1].startswith("课本 "):
        raise ValueError("Unexpected Year 2 standards/references")
    details = [refs[0], table.cell(1,1).text, table.cell(6,1).text, refs[1]]
    activity_paras = list(table.cell(3,1).paragraphs) + list(table.cell(4,1).paragraphs)
    if len(activity_paras) != 3:
        raise ValueError("Unexpected Year 2 activity count")
    activities = []
    for i, p in enumerate(activity_paras, 1):
        if not p.runs or not p.runs[0].bold:
            raise ValueError("Missing Year 2 source role label")
        label = p.runs[0].text.strip()
        body = p.text[len(p.runs[0].text):]
        if not label.startswith("活动 " + str(i)) or not body.strip():
            raise ValueError("Unexpected Year 2 activity")
        activities.append((label, body))
    phases = [("导入", table.cell(2,1).text), *activities, ("总结", table.cell(5,1).text)]
    # Validate the original educational text, excluding only source timing labels.
    return details, phases, ""


def _extract(source, lesson, year):
    ps = [p.text.strip() for p in source.paragraphs if p.text.strip()]
    if year == 2:
        return _extract_year2(source, lesson, ps)
    if len(ps) != 9 or not re.match(r"^PdP\s+%03d\b" % lesson["pdp"], ps[1]):
        raise ValueError("Unexpected source header/paragraphs")
    if ps[2] != lesson["topic"] or not ps[3].startswith("日期 Tarikh "):
        raise ValueError("Source identity mismatch")
    if not ps[8].startswith("教学反思"):
        raise ValueError("Unexpected source reflection")
    if len(source.tables) != 1:
        raise ValueError("Unexpected source table count")
    table = source.tables[0]
    n = len(table.columns)
    if len(table.rows) != 6 or n not in (2, 3):
        raise ValueError("Unexpected phase table dimensions")
    if n == 3 and table.cell(0, 1).text.strip() not in ("", "分钟"):
        raise ValueError("Unexpected phase minute column")
    phases = []
    for row in table.rows[1:]:
        label = MINUTES.sub("", row.cells[0].text).strip()
        content = row.cells[-1].text
        if not label or not content.strip():
            raise ValueError("Empty source phase")
        phases.append((label, content))
    # Keep all source academic paragraphs, including full original labels and notes.
    return ps[4:8], phases, ps[8][len("教学反思"):].lstrip("：: ")


def convert(source, lesson, year, teacher=None):
    if year not in (2, 3):
        raise ValueError("Unsupported year")
    teacher = teacher or {}
    details, phases, original_reflection = _extract(source, lesson, year)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = sec.right_margin = Mm(14)
    sec.top_margin = sec.bottom_margin = Mm(12)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(p, "每日教学计划", True, 14)
    hero = _table(doc, 118, 64)
    a, b = _row(hero, 118, 64)
    _fill(a, HEADER)
    _fill(b, "F1F3F5")
    _line(a, "数学（华小）", True, True, 12)
    _line(a, str(year) + " 年级")
    _line(a, lesson["unit"])
    _line(a, lesson["topic"], True)
    for i, (label, key) in enumerate((("班级 Kelas", "class"), ("日期 Tarikh", "date"),
                                     ("时间 Masa", "time"), ("学生人数 Bilangan Murid", "students"))):
        value = teacher.get(key)
        p = b.paragraphs[0] if i == 0 else b.add_paragraph()
        _run(p, label + "：", True)
        _run(p, "" if value is None else str(value))
    grid = _table(doc, LABEL_WIDTH, WIDTH-LABEL_WIDTH)
    for label, text in zip(("内容与学习标准", "学习目标", "教具", "课本与活动本"), details):
        _value(grid, label, text)
    _value(grid, "导入", phases[0][1])
    main = _value(grid, "主要活动", "")
    for i, (label, text) in enumerate(phases[1:4], 1):
        _line(main, label, True, first=i == 1)
        _line(main, text)
    _value(grid, "总结", phases[4][1])
    reflection = teacher.get("reflection")
    text = original_reflection
    if reflection:
        text = "\n".join(x for x in (text, str(reflection)) if x)
    _value(grid, "教学反思", text)
    all_text = "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
    for value in [*details, *(p[1] for p in phases), *(p[0] for p in phases[1:4]),
                  original_reflection, str(reflection or "")]:
        if value.strip() and value not in all_text:
            raise ValueError("Source content lost")
    return doc


def word_for(year, lesson, teacher=None):
    from staging.matematik_sjkc.tahun_2 import rph as y2
    from staging.matematik_sjkc.tahun_3 import rph as y3
    source = {2: y2, 3: y3}[year]
    if source.resolve(lesson["unit_number"], lesson["pdp"]) != lesson:
        raise ValueError("Lesson not in resolved source")
    _, raw = source.render(lesson, "word", {})
    doc = convert(Document(BytesIO(raw)), lesson, year, teacher)
    output = BytesIO()
    doc.save(output)
    return output.getvalue()


def pdf_for_qa(word):
    """Offline only; render Word directly, not PDF overlays."""
    with TemporaryDirectory() as directory:
        root = Path(directory)
        src = root / "lesson.docx"
        src.write_bytes(word)
        subprocess.run(["libreoffice", "-env:UserInstallation=" + (root / "profile").as_uri(),
                        "--headless", "--convert-to", "pdf", "--outdir", str(root), str(src)],
                       check=True, capture_output=True, timeout=60)
        result = (root / "lesson.pdf").read_bytes()
        if not result.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF")
        return result
