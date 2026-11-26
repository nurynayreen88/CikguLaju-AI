"""Conservative formatting for source-extracted RPT body cells, not academic edits."""
import re
from docx.shared import Pt

BOUNDARY=re.compile(r"^(?:\d+\.\d+(?:\.\d+)*(?:\s|$|\()|(?:SK|SP|CS|LS|PdP|Lesson|Unit|Tema|Tajuk|Topik|MAIN|COMPLEMENTARY|Main Skill|Complementary Skill|Learning Standard|Content Standard|Textbook|Student.?s Book|Workbook|Activity Book|TB|SB|WB|AB|BBM|Bahan|Catatan|Rujukan|EMK|KBAT|PBD|Pentaksiran|Evidens|Nilai)\b)",re.I)
IDENTIFIER=re.compile(r"^(?:\d+\.\d+(?:\.\d+)*(?:\([ivx]+\))?|(?:SK|SP|CS|LS)\s+\d+\.\d+(?:\.\d+)*|(?:PdP|Lesson)\s*[:]?\s*\d+)",re.I)
def norm(v):return re.sub(r"\s+"," ",v).strip()
def reflow(lines):
    out=[]
    for line in lines:
        v=line.strip()
        if not v:continue
        if not out or BOUNDARY.match(v):out.append(v)
        else:out[-1]+=" "+v
    assert norm(" ".join(out))==norm(" ".join(lines))
    return out
def format_source_cell(cell,lines,fill,*,size=8.5,preserve=False):
    fill(cell,lines if preserve else reflow(lines))
    for p in cell.paragraphs:
        p.paragraph_format.keep_together=True
        m=IDENTIFIER.match(p.text)
        if not m:continue
        val=p.text;p.clear()
        for text,bold in ((m.group(),True),(val[m.end():],False)):
            if text:
                run=p.add_run(text);run.bold=bold;run.font.name="Arial";run.font.size=Pt(size)
