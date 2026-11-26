"""Repack existing RTL PDF vector rows without re-typesetting Arabic/Jawi."""
import argparse,json
from pathlib import Path
from collections import Counter,defaultdict
from hashlib import sha256
from datetime import date
import re
import fitz
from scripts.reschedule_web_rpt_teaching_weeks import (
    pdf_rows,isolate_clip,append_row,add_page,print_week,TOP,BOTTOM,LEFT,CELL_WIDTH
)
from scripts.build_web_rpt_weekly_suggestions import read_weeks,SUBJECTS
ROOT=Path("rpt_2027/web_2027_pdfs")
def build(subject,year,out):
    key=f"{subject}:{year}"
    entry=json.loads((ROOT/"manifest.json").read_text())["files"][key]
    source=ROOT/entry["path"]
    assert sha256(source.read_bytes()).hexdigest()==entry["sha256"]
    dates,assignments=read_weeks(source,SUBJECTS[subject])
    weekmap={ (c,n):w for w,groups in assignments.items() for c,nums in groups.items() for n in nums}
    with fitz.open(source) as old,fitz.open() as result,fitz.open() as fragments:
        rows=pdf_rows(old,True)
        assert len(rows)==len(weekmap) and {r[0] for r in rows}==set(weekmap)
        groups=defaultdict(list)
        for row in rows:groups[weekmap[row[0]]].append(row)
        closures={}
        for p in list(old)[1:]:
            for d in p.get_drawings():
                rect=d["rect"]
                if d["type"] not in ("f","fs") or abs(rect.x1-(p.rect.width-23))>.1 or abs(rect.width-105)>.1:continue
                label=p.get_text(clip=rect)
                if "Cuti sekolah" not in label:continue
                match=re.search(r"\bM(\d{2})\b",label)
                assert match
                w=int(match[1])
                clip=fitz.Rect(LEFT,rect.y0,rect.x1,rect.y1)
                assert w not in closures
                closures[w]=(p.number,clip)
        result.insert_pdf(old,from_page=0,to_page=0)
        rect=old[1].rect
        isolate_clip(fragments,old,1,fitz.Rect(0,0,rect.width,TOP))
        isolate_clip(fragments,old,1,fitz.Rect(0,558,755,rect.height))
        row_fragments={i:isolate_clip(fragments,old,p,c) for i,p,c in rows}
        close_fragments={w:isolate_clip(fragments,old,p,c) for w,(p,c) in closures.items()}
        page=add_page(result,fragments);y=TOP;copied=[]
        font=fitz.Font("helv")
        for week in sorted(set(groups)|set(closures)):
            if week in closures:
                p,clip=closures[week]
                if y+clip.height>BOTTOM:page=add_page(result,fragments);y=TOP
                target=fitz.Rect(clip.x0,y,clip.x1,y+clip.height)
                page.show_pdf_page(target,fragments,close_fragments[week],clip=clip)
                copied.append((page.number,target,p,clip))
                y=target.y1
                continue
            pending=list(groups[week])
            display=[date.fromisoformat(d).strftime("%d/%m/%Y") for d in dates[week]]
            while pending:
                capacity=BOTTOM-y
                h=0;count=0
                for row in pending:
                    if h+row[2].height>capacity+.001:break
                    h+=row[2].height;count+=1
                # Allow a week to continue on another page, but leave enough
                # vertical space for the repeated week/date cell.
                if not count or (h<52 and y>TOP):
                    page=add_page(result,fragments);y=TOP;continue
                assert h>=38,(key,week,h)
                start=y
                for row in pending[:count]:
                    y=append_row(page,old,fragments,row_fragments,row,y,copied)
                x=rect.width-23-CELL_WIDTH
                print_week(page,fitz.Rect(x,start,x+CELL_WIDTH,y),week,display,font)
                pending=pending[count:]
                if pending:page=add_page(result,fragments);y=TOP
        result.set_metadata(old.metadata)
        target=out/f"RPT_{subject}_tahun_{year}_2027.pdf"
        result.save(target,garbage=4,deflate=True,clean=True,use_objstms=1)
        with fitz.open(target) as new:
            assert old[0].get_pixmap().samples==new[0].get_pixmap().samples
            for page_no,clip,old_no,old_clip in copied:
                before=old[old_no].get_text(clip=old_clip)
                after=new[page_no].get_text(clip=clip)
                assert before==after,(key,old_no,page_no,list(old_clip),list(clip),repr(before),repr(after))
            assert Counter(l["uri"] for p in old for l in p.get_links())==Counter(l["uri"] for p in new for l in p.get_links())
            assert len(new)<=len(old)
            for p in new:
                assert p.get_pixmap(matrix=fitz.Matrix(.6,.6),alpha=False).width>0
            assert len(pdf_rows(new,True))==len(rows)
            new_dates,new_assignments=read_weeks(target,SUBJECTS[subject])
            assert new_dates==dates and new_assignments==assignments
            print(json.dumps({"key":key,"source_pages":len(old),"pages":len(new),"rows":len(rows),"closures":len(closures),"status":"VECTOR_ROW_TEXT_AND_SCHEDULE_PARITY"}),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--subject",choices=("pendidikan_islam","bahasa_arab"),required=True);p.add_argument("--year",type=int,choices=range(2,7),required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);build(a.subject,a.year,a.out)
