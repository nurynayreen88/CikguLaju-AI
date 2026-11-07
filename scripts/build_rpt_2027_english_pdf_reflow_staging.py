"""Read the published English 2027 source PDF (160 Lessons/year) and reflow only.

Each English lesson lives in the 4-column source PDF with explicit
Main/Complementary content and learning standards. The new five-column
preview separates CS (SK) and LS (SP); missing codes remain labelled
teacher-choice, never invented. Source PDFs are immutable.
"""
from __future__ import annotations
import re
from pathlib import Path
import fitz

from rpt_2027.common.format_2026_layout_preview import build_preview,validate_rows
from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"staging/rpt_2027_seragam_2026/english_reflow_DRAF"


def plain(value):
    return re.sub(r"\s+"," ",str(value or "")).strip()


def lesson_labels(page):
    words=page.get_text("words")
    seen={}
    for x0,y0,x1,y1,value,*_ in words:
        if value.upper()!="LESSON:" or not 110<x0<230:
            continue
        matches=[w for w in words if
                 w[4].isdigit() and
                 abs(w[1]-y0)<2 and
                 0 < w[0]-x1 < 11]
        if len(matches)!=1:
            raise ValueError("English PDF ambiguous lesson number")
        n=int(matches[0][4])
        if n in seen:
            raise ValueError("English repeated label on one page")
        seen[n]=(y0,y1)
    return sorted(seen.items(),key=lambda x:x[1][0])


def lines_from_clip(page,x0,y0,x1,y1):
    return [x.strip() for x in
            page.get_text("text",clip=fitz.Rect(x0,max(0,y0),x1,min(page.rect.height,y1)),
                          sort=True).splitlines() if x.strip()]


def parse_standards(lines):
    sk,sp=[],[]
    last=None
    extra=[]
    non_standard=False
    for line in lines:
        upper=line.upper()
        if upper in ("MAIN","COMPLEMENTARY"):
            last=None
            continue
        if "LANGUAGE FOCUS:" in upper:
            non_standard=True
            extra.append(line)
            last=None
            continue
        if non_standard:
            extra.append(line)
            continue
        m=re.match(r"^(\d{1,2}\.\d{1,2}(?:\.\d{1,3})?)\s+(.+)$",line)
        if m:
            code=m.group(1)
            target=sp if code.count(".")==2 else sk
            target.append(code+" "+m.group(2).strip())
            last=target
        elif last and last[-1] and not line.upper().startswith("MAIN"):
            last[-1]+=" "+line
        else:
            extra.append(line)
    return sk,sp,extra


def english_records(year):
    if year not in range(2,7):
        raise ValueError("English RPT supported Years 2–6 only")
    path=ROOT/f"rpt_2027/english/RPT_ENGLISH_TAHUN_{year}_2027_UNTUK_GURU.pdf"
    master=load_calendar_weeks()
    result=[]
    known_weeks=set()
    with fitz.open(path) as pdf:
        if pdf.page_count < 41:
            raise ValueError("English source PDF incomplete")
        for page_index in range(1,len(pdf)):
            pg=pdf[page_index]
            labeled=lesson_labels(pg)
            if not labeled:
                continue
            # Source PDF may spill a 4-Lesson week onto another physical
            # page (notably Year 3). PDF page index is not a week identity.
            printed_weeks=[
                int(x) for x in re.findall(
                    r"\bWEEK\s+(\d{1,2})\b",
                    pg.get_text("text",clip=fitz.Rect(0,45,126,550)),
                    flags=re.IGNORECASE
                )
            ]
            known_weeks.update(printed_weeks)
            # Main and Complementary are physically in x292–650, with
            # lesson/Theme/Topic in x129–288 and reference in x655–810.
            for i,(number,(y0,y1)) in enumerate(labeled):
                if number!=len(result)+1:
                    raise ValueError(f"English T{year}: missing Lesson before {number}")
                week=f"M{(number-1)//4+1:02d}"
                if week not in master["A"]:
                    raise ValueError("English lesson exceeds original 40-week 4-Lesson slots")
                if printed_weeks and (number-1)//4+1 not in printed_weeks:
                    # Some PDF pages can hold two week groups, so only flag
                    # an actual printed week conflict; never silently relabel.
                    raise ValueError(
                        f"English T{year} L{number:03d} page {page_index+1}: "
                        f"source printed weeks {printed_weeks} disagree with {week}")
                top=y0-13.8
                bottom=(labeled[i+1][1][0]-13.8 if i+1<len(labeled)
                        else 552)
                if bottom<=top:
                    raise ValueError("English PDF row crop overlaps")
                mid=lines_from_clip(pg,127,top,287,bottom)
                st=lines_from_clip(pg,290,top,653,bottom)
                notes=lines_from_clip(pg,656,top,811,bottom)
                # Some topic phrases are wrapped; extract the explicit labels
                # from their original column rather than inventing a title.
                unit_line=" ".join(x for x in mid if x.upper().startswith("UNIT / TOPIC:"))
                theme_line=" ".join(x for x in mid if x.upper().startswith("THEME:"))
                focus_line=" ".join(x for x in mid if x.upper().startswith("FOCUS:"))
                if not unit_line:
                    raise ValueError(f"English T{year} L{number:03d}: missing UNIT/TOPIC")
                sk,sp,extra=parse_standards(st)
                if not sk or not sp:
                    # Where source omits standards (teacher-choice), do not
                    # invent official codes. Keep explicit release warning.
                    if sk or sp:
                        raise ValueError(f"English T{year} L{number:03d}: partial CS/LS extraction")
                    sk=["PILIHAN GURU — tiada CS tetap dalam PDF sumber"]
                    sp=["PILIHAN GURU — tiada LS tetap dalam PDF sumber"]
                refs=plain(" ".join(notes))
                warning=" | Main/Complementary codes from source SOW, not a new DSKP choice."
                result.append(dict(
                    id=f"{number:03d}",display_id=f"Lesson {number:03d}",
                    week=week,
                    unit=plain(unit_line),
                    topic=plain(theme_line+" | "+focus_line),
                    sk=sk[0].split()[0],
                    sp=sp[0].split()[0],
                    sk_display="\n".join(plain(x) for x in sk),
                    sp_display="\n".join(plain(x) for x in sp),
                    note=(refs+" | "+plain(" ".join(extra))+warning)[:420],
                    source_pdf=path.name,
                    a_start=master["A"][week][0],a_end=master["A"][week][1],
                    b_start=master["B"][week][0],b_end=master["B"][week][1]
                ))
    if known_weeks != set(range(1,41)):
        raise ValueError(f"English T{year} printed RPT week labels not 1-40: {sorted(known_weeks)}")
    if len(result)!=160:
        raise ValueError(f"English T{year}: expected 160 SOW Lessons, got {len(result)}")
    validate_rows("english",year,result)
    return result


def build_all(out=OUT):
    files=[]
    for y in range(2,7):
        rows=english_records(y)
        p=Path(out)/f"CIKGULAJU_RPT_ENGLISH_TAHUN_{y}_2027_LIMA_LAJUR_DRAF.pdf"
        build_preview("english",y,rows,p,max_span_rows=2)
        files.append((y,len(rows),p))
    return files


if __name__=="__main__":
    for y,n,file in build_all():
        print(f"ENGLISH_REBUILT Year {y}: {n} lessons => {file}")
