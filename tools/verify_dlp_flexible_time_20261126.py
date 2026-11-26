"""Test actual released DLP RPT downloads without touching curriculum sources."""
import os,re
from pathlib import Path
from io import BytesIO
from collections import Counter
import fitz
from docx import Document
from tools.build_rpt_dlp_native_20261126 import PINS, document_path
from tools.build_rpt_dlp_full_standards_20261126 import build_word
from web.rpt_compact_pdf import read_full_standards_dlp,dlp_whole_week_release
from web.rpt_dlp_flexible_time import word_without_fixed_minutes,pdf_without_fixed_minutes,DURATION

def test_all():
    root=Path("rpt_2027")
    os.environ["CIKGULAJU_RPT_FULL_STANDARDS_DLP"]="1"
    for key in PINS:
        subject,year=key.split(":");year=int(year)
        raw=document_path(subject,year,root=root/"dlp").read_bytes()
        approved=read_full_standards_dlp(subject,year,raw,root=root)
        assert approved,key
        old_pdf=approved[0]
        if dlp_whole_week_release(root):
            # Current published calendar already omits fixed per-lesson durations.
            # Verify its real bytes instead of applying a retired transform twice.
            with fitz.open(stream=old_pdf,filetype="pdf") as pdf:
                for page in list(pdf)[1:-1]:
                    assert not any(DURATION.fullmatch(t.strip()) for t in page.get_text().splitlines()),(key,page.number)
                    assert "Textbook" in page.get_text(),(key,page.number)
            print("FLEXIBLE_TIME_ALREADY_RELEASED",key,flush=True)
            continue
        old_word=build_word(subject,year,root=root)[0]
        new_word=word_without_fixed_minutes(old_word)
        a,b=Document(BytesIO(old_word)),Document(BytesIO(new_word))
        assert len(a.tables)==len(b.tables)
        assert [p.text for p in a.paragraphs]==[p.text for p in b.paragraphs]
        n=0
        for ta,tb in zip(a.tables,b.tables):
            assert len(ta.rows)==len(tb.rows)
            for i,(ra,rb) in enumerate(zip(ta.rows,tb.rows)):
                for j,(ca,cb) in enumerate(zip(ra.cells,rb.cells)):
                    if len(ta.columns)==6 and j==5:
                        if i==0:assert cb.text=="Textbook"
                        else:
                            lines=ca.text.splitlines()
                            keep=[l for l in lines if not DURATION.fullmatch(l.strip())]
                            n+=len(lines)-len(keep)
                            assert cb.text=="\n".join(keep),(key,i,ca.text,cb.text)
                    else:assert ca.text==cb.text,(key,i,j)
        assert n
        new_pdf=pdf_without_fixed_minutes(old_pdf)
        with fitz.open(stream=old_pdf,filetype="pdf") as a,fitz.open(stream=new_pdf,filetype="pdf") as b:
            assert len(a)==len(b)
            assert a[0].get_pixmap().samples==b[0].get_pixmap().samples,key
            assert a[-1].get_pixmap().samples==b[-1].get_pixmap().samples,key
            count=0
            for x,y in zip(list(a)[1:-1],list(b)[1:-1]):
                assert x.rect==y.rect
                before=x.get_text().splitlines();after=y.get_text().splitlines()
                assert not any(DURATION.fullmatch(t.strip()) for t in after),(key,y.number)
                assert "Time" not in [t.strip() for t in after],(key,y.number)
                assert len(x.get_drawings())==len(y.get_drawings()),(key,y.number,"grid changed")
                # No missing academic words, excluding exact removed durations and header slash.
                clean=lambda lines:Counter(" ".join(t for t in lines if not DURATION.fullmatch(t.strip()) and t.strip()!="Time").replace("Textbook /","Textbook").split())
                assert clean(before)==clean(after),(key,y.number,clean(before)-clean(after),clean(after)-clean(before))
                count+=sum(bool(DURATION.fullmatch(t.strip())) for t in before)
            assert count==n,(key,count,n)
        print("FLEXIBLE_TIME_OK",key,n,flush=True)

if __name__=="__main__":test_all()
