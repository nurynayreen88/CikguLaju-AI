"""Offline QA: 82 supplemental Arabic RPH; never publish."""
import json
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from web.arabic_rph_word import render_arabic_word, _paragraph
def main():
    out=Path("qa-arabic-82");out.mkdir(exist_ok=True)
    count=0
    for y in range(2,7):
        records=json.loads(Path(f"rph_standalone/bahasa_arab/proposed_2027/year{y}_extra_30min_20261125.json").read_text(encoding="utf8"))["records"]
        for r in records:
            assert r["minutes"]==30 and not r["ready"]
            plan=dict(year=y,topic=r["unit_name"],focus=r["focus"],pages="",sk=r["sk"],sp=r["sp"],content_standard="",learning_standard="",objective=r["objective"],success=r["criterion"],induction=r["intro"],activity_1=r["activity1"],activity_2=r["activity2"],assessment=r["assessment"],closure=r["close"],materials=r["materials"],reflection=r["reflection"],activity_1_note="")
            dest=out/f"BA_T{y}_{r['proposed_pdp']:03d}.docx"
            render_arabic_word(plan,("","","","",""),"",dest)
            d=Document(dest)
            _paragraph(d.tables[0].cell(0,0).add_paragraph(),"مدة الدرس: ٣٠ دقيقة",size=10)
            for i,k in ((2,"title1"),(3,"title2")):
                _paragraph(d.tables[2].cell(i,1).paragraphs[0].insert_paragraph_before(),r[k],bold=True,size=9)
            for i in (2,3,4):d.tables[2].cell(i,2).text=""
            c=d.tables[3].cell(1,1);c.text=""
            _paragraph(c.paragraphs[0],"معايير المنهج، الصفحة "+str(r["dskp_printed_page"])+"؛ نشاط تعزيزي من إعداد المعلم.",size=9)
            for t in d.tables[1:]:
                for row in t.rows:
                    for c in row.cells:
                        for p in c.paragraphs:
                            for run in p.runs:
                                run.font.size=Pt(9)
                                z=run._r.get_or_add_rPr().find(qn("w:szCs"))
                                if z is not None:z.set(qn("w:val"),"18")
            d.core_properties.comments="Review only; exact textbook page and approval pending."
            d.save(dest)
            text="\n".join(c.text for t in Document(dest).tables for row in t.rows for c in row.cells)
            for k in ("focus","criterion","title1","activity1","title2","activity2","assessment","reflection"):
                assert r[k] in text,(y,r["proposed_pdp"],k)
            count+=1
    assert count==82
    print("82 supplemental Word candidates generated")
if __name__=="__main__":main()
