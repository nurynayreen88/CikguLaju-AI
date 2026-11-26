"""Presentation only: remove prescriptive per-lesson durations, preserve source PDFs and RPH IDs."""
import re
from io import BytesIO
import fitz
from docx import Document

DURATION=re.compile(r"^\d+\s*min(?:utes)?$",re.I)
HEADERS={"Textbook /\nTime":"Textbook","Book reference / Time":"Book reference","Textbook / Time":"Textbook"}

def word_without_fixed_minutes(blob):
    doc=Document(BytesIO(blob))
    removed=0
    for table in doc.tables:
        if len(table.columns) not in (5,6):continue
        cell=table.rows[0].cells[-1]
        label=cell.text.strip()
        if label not in HEADERS:continue
        # Retain the existing font and paragraph style.
        p=cell.paragraphs[0]
        for r in p.runs:r.text=""
        if p.runs:p.runs[0].text=HEADERS[label]
        else:p.add_run(HEADERS[label])
        for extra in cell.paragraphs[1:]:extra._p.getparent().remove(extra._p)
        for row in table.rows[1:]:
            c=row.cells[-1]
            for p in list(c.paragraphs):
                if DURATION.fullmatch(p.text.strip()):
                    removed+=1
                    if len(c.paragraphs)==1:p.clear()
                    else:p._p.getparent().remove(p._p)
    assert removed,"No recognized DLP lesson durations"
    out=BytesIO();doc.save(out);return out.getvalue()

def pdf_without_fixed_minutes(raw):
    # Remove only exact duration glyphs in the final reference column, not
    # graphics, table lines, images, or mathematical statements. The original
    # approved PDF remains untouched; appendix annual totals are retained.
    removed=0
    with fitz.open(stream=raw,filetype="pdf") as doc:
        for page in list(doc)[1:]:
            text=page.get_text()
            if "Teaching information and source references" in text:continue
            if "Lesson / Unit" not in text:continue
            hits=[]
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    for span in line["spans"]:
                        val=span["text"].strip();box=fitz.Rect(span["bbox"])
                        if box.x0<page.rect.width*.83:continue
                        if DURATION.fullmatch(val):
                            hits.append((box,None));removed+=1
                        elif val in ("Time","Textbook /","Book reference / Time","Textbook / Time"):
                            # Preserve the base label. Remove just slash/time
                            # via exact glyph positions instead of replacing text.
                            if val=="Time":hits.append((box,None));continue
                            for word in (" / Time"," /"):
                                if word in val:
                                    regions=page.search_for(word.strip(),clip=box+(-1,-1,1,1))
                                    if regions:
                                        hits.extend((r,None) for r in regions)
                                        break
            if hits:
                for box,_ in hits:page.add_redact_annot(box,fill=False,cross_out=False)
                page.apply_redactions(images=0,graphics=0,text=0)
        assert removed,"No recognized DLP PDF lesson durations"
        return doc.tobytes(garbage=4,deflate=True)
