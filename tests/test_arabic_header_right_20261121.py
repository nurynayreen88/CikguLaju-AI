"""Arabic RPH: right-side header and RTL content survive format changes."""
from io import BytesIO

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_TABLE_DIRECTION
from docx.oxml.ns import qn

from web.arabic_rph_word import render_arabic_word


def test_arabic_teacher_header_right_and_source_fields_preserved():
    plan = {
        "year": 2, "lesson": 1, "topic": "المدرسة", "focus": "الفصل",
        "pages": "2 & 4", "sk": "1.1", "sp": "1.1.1",
        "content_standard": "الاستماع", "learning_standard": "يسمع التلميذ",
        "objective": "يذكر التلميذ الكلمات", "success": "يذكر كلمتين",
        "induction": "يشاهد الصور", "activity_1": "يستمع إلى الكلمات",
        "activity_2": "يردد الكلمات", "assessment": "يسمي صورتين",
        "closure": "يلخص النشاط", "materials": "بطاقات", "reflection": "متابعة",
    }
    out = BytesIO()
    render_arabic_word(plan, ("2 AMANAH", "", "08:00 - 09:00", "28", None), "متابعة", out)
    doc = Document(BytesIO(out.getvalue()))
    assert len(doc.tables) == 4
    title_props = doc.paragraphs[0]._p.pPr
    assert title_props.find(qn("w:pBdr")) is not None
    assert title_props.find(qn("w:shd")).get(qn("w:fill")) == "FCE8D8"
    header = doc.tables[0]
    assert header.alignment == WD_TABLE_ALIGNMENT.RIGHT
    assert header.table_direction == WD_TABLE_DIRECTION.RTL
    assert [r.cells[0].text for r in header.rows] == [
        "الفصل", "التاريخ", "الوقت", "عدد التلاميذ",
    ]
    assert [r.cells[1].text for r in header.rows] == [
        "2 AMANAH", "", "08:00 - 09:00", "28",
    ]
    for row in header.rows:
        assert row.cells[0]._tc.tcPr.find(qn("w:shd")) is not None
    body = " ".join(
        c.text for table in doc.tables[1:] for row in table.rows for c in row.cells
    )
    for value in ("الاستماع", "يسمع التلميذ", "يذكر كلمتين",
                  "يستمع إلى الكلمات", "بطاقات", "متابعة"):
        assert value in body
