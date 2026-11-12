"""Reflow five source Math RPT 2027 PDFs (117 numbered Lessons/year) to A4 5 columns.

Source PDF itself is the authority for sequence, week, SK/SP and brief lesson
notes. No changes to source PDF, RPH, runtime or database.
"""
from __future__ import annotations
import re
from pathlib import Path
import fitz

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from rpt_2027.common.format_2026_layout_preview import build_preview,validate_rows

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"staging/rpt_2027_seragam_2026/matematik_reflow_DRAF"

def labels_from_words(page):
    words=page.get_text("words")
    lessons=[]
    weeks=[]
    for x0,y0,x1,y1,t,*_ in words:
        if t=="Lesson" and 30<x0<90:
            opts=[v for v in words if v[4].isdigit() and len(v[4])==3
                  and abs(v[1]-y0)<1.8 and 0<v[0]-x1<14]
            if len(opts)!=1:
                raise ValueError("Math original lesson identity missing in source row")
            lessons.append((int(opts[0][4]),y0))
        if t=="MINGGU" and 25<x0<75 and y0>150:
            opts=[v for v in words if re.fullmatch(r"\d{2}",v[4])
                  and abs(v[1]-y0)<1.9 and 0<v[0]-x1<16]
            if len(opts)==1:
                weeks.append((int(opts[0][4]),y0))
    if len(set(v[0] for v in lessons))!=len(lessons):
        raise ValueError("Math duplicated lesson number on page")
    return sorted(lessons,key=lambda x:x[1]),sorted(weeks,key=lambda x:x[1])


def clip_lines(page,x0,y0,x1,y1):
    return [x.strip() for x in page.get_text(
        "text",sort=True,clip=fitz.Rect(x0,max(0,y0),x1,min(page.rect.height,y1))
    ).splitlines() if x.strip()]


def clean(s):
    return re.sub(r"\s+"," ",s).strip()


def math_records(year):
    if year not in range(2,7):
        raise ValueError("Math RPT supports Years 2-6")
    path=ROOT/f"rpt_2027/matematik/RPT_Matematik_Tahun_{year}_2027_v28_SEMENTARA.pdf"
    cal=load_calendar_weeks()
    rows=[]
    current_week=None
    with fitz.open(path) as pdf:
        if pdf.page_count<15:
            raise ValueError("Math source PDF unusually short")
        for page_no,page in enumerate(pdf):
            lessons,weeks=labels_from_words(page)
            if not lessons:
                if weeks:
                    current_week=f"M{weeks[-1][0]:02d}"
                continue
            for n,y in lessons:
                if n!=len(rows)+1:
                    raise ValueError(f"Math T{year}: source missing Lesson before {n}")
                nearest=[w for w in weeks if w[1]<=y]
                if nearest:
                    current_week=f"M{nearest[-1][0]:02d}"
                if current_week is None or current_week not in cal["A"]:
                    raise ValueError(f"Math T{year} lesson {n}: no original 2027 week")
                candidates=[yy for _,yy in lessons if yy>y]
                candidates.extend(yy for _,yy in weeks if yy>y)
                bottom=min(candidates) - 1.0 if candidates else 555
                # Source PDF has compact columns:
                # original Unit: x101–230; SK: x232–321; SP: x324–383;
                # activity/PBD/BBM: x385–810.
                top=y-1.0
                if bottom<=top:
                    raise ValueError("Math source lesson crop invalid")
                unit=clean(" ".join(clip_lines(page,101,top,230,bottom)))
                sk=clean(" ".join(clip_lines(page,232,top,321,bottom)))
                sp=clean(" ".join(clip_lines(page,324,top,383,bottom)))
                note=clean(" ".join(clip_lines(page,385,top,810,bottom)))
                sk_code=re.match(r"(\d+(?:\.\d+)+)",sk)
                sp_code=re.match(r"(\d+(?:\.\d+)+)",sp)
                if not sk_code or not sp_code or not note or not unit:
                    raise ValueError(f"Math T{year} Lesson{n:03d}: source SK/SP/Unit/PBD crop empty")
                rows.append(dict(
                    id=f"{n:03d}",display_id=f"Lesson {n:03d}",
                    week=current_week,unit=unit,
                    topic="",sk=sk_code.group(1),sp=sp_code.group(1),
                    sk_display=sk,sp_display=sp,
                    note=note[:420],
                    source_pdf=path.name,
                    a_start=cal["A"][current_week][0],a_end=cal["A"][current_week][1],
                    b_start=cal["B"][current_week][0],b_end=cal["B"][current_week][1]
                ))
    if len(rows)!=117:
        raise ValueError(f"Math T{year}: {len(rows)}/117 numbered source lessons")
    validate_rows("matematik",year,rows)
    return rows


def build_all(out=OUT):
    files=[]
    for year in range(2,7):
        rows=math_records(year)
        path=Path(out)/f"CIKGULAJU_RPT_MATEMATIK_TAHUN_{year}_2027_LIMA_LAJUR_DRAF.pdf"
        build_preview("matematik",year,rows,path,max_span_rows=2)
        files.append((year,len(rows),path))
    return files


if __name__=="__main__":
    for y,n,path in build_all():
        print(f"MATH_REBUILT Year {y}: {n} lessons => {path}")
