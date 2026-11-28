"""Independent PDF layout QA for 184 matched Science draft records, not delivery."""
import argparse
import json
from html import escape
from pathlib import Path
from web.rph_5p_v5_layout import MS_LABELS, PHASE_KEYS, FIELDS, Palette, validate
from tools.audit_science_5p_native_162_print_20261128 import ROOT, DRAFT, COUNTS, inputs, fixture, load
from tools.audit_science_5p_layout_fixtures_20261128 import inspect_pdf

# Same renderer logic as previously tested Y5/Y6 QA; no production imports or routes.
def render_pdf(source,c,raw,profile,palette,subject_heading):
    """Native one-page PDF; no external process, no truncation or scaling."""
    import fitz
    validate(source,c,source_bytes=raw)
    labels=MS_LABELS
    w,h=595.28,841.89
    x0,x1,x2=42.52,161.58,552.76
    def rgb(hexstr):return tuple(int(hexstr[i:i+2],16)/255 for i in (0,2,4))
    border=rgb(palette.border)
    fills={k:rgb(getattr(palette,k)) for k in ("title","header","label")}
    def html(v,b=False):
        s=escape(str(v),quote=False).replace("\n","<br/>")
        return "<b>"+s+"</b>" if b else s
    def css(size,center=False):
        return f"body{{font-family:sans-serif;font-size:{size}pt;line-height:1.13;margin:0;padding:0;color:#17232b;"+("text-align:center;" if center else "")+"}p{margin:0;padding:0;}"
    def measure(v,width,size,center=False):
        more,box=fitz.Story(v,user_css=css(size,center)).place(fitz.Rect(0,0,width-10,780))
        if more:raise ValueError("Ruang 5P tidak muat")
        return box[3]-box[1]+2
    def cell(page,l,t,r,b,v,size,fill=None,center=False):
        page.draw_rect(fitz.Rect(l,t,r,b),color=border,fill=fills.get(fill,(1,1,1)),width=.55)
        mh=measure(v,r-l,size,center)
        y=t+(b-t-mh)/2
        spare,scale=page.insert_htmlbox(fitz.Rect(l+5,y,r-5,y+mh),v,css=css(size,center),scale_low=1)
        if spare<0 or scale!=1:raise ValueError("Teks 5P tidak muat")
    d=fitz.open()
    try:
        page=d.new_page(width=w,height=h);y=36
        def row(left,right,*,fill="label",rightfill=None,size=9):
            nonlocal y
            height=max(measure(left,x1-x0,size),measure(right,x2-x1,size))+5
            if y+height>h-36:raise ValueError("RPH 5P tidak muat satu A4")
            cell(page,x0,y,x1,y+height,left,size,fill)
            cell(page,x1,y,x2,y+height,right,size,rightfill)
            y+=height
        title=html(labels[0],True);height=measure(title,x2-x0,14,True)+7
        cell(page,x0,y,x2,y+height,title,14,"title",True);y+=height
        info="\n".join(f"{label}: {profile[key]}".rstrip() for label,key in zip(labels[1:5],("class","date","time","students")))
        row(html(info,True),html(subject_heading,True),fill="header",rightfill="header")
        for i,key in enumerate(FIELDS[:5],5):
            row(html(labels[i],True),html(source[key]))
        steps=[]
        for i,key in enumerate(PHASE_KEYS):
            steps.extend([(html(labels[11+i],True),"label"),(html(c["phases"][key]),None)])
        heights=[measure(v,x2-x1,9)+5 for v,_ in steps]
        total=sum(heights)
        if y+total>h-36:raise ValueError("Aktiviti 5P tidak muat")
        cell(page,x0,y,x1,y+total,html(labels[10],True),9,"label",True)
        for (value,fill),height in zip(steps,heights):
            cell(page,x1,y,x2,y+height,value,9,fill);y+=height
        for i,key in enumerate(FIELDS[5:],16):
            row(html(labels[i],True),html(source[key] if key!="reflection" else source[key] or "\u00a0\n\u00a0\n\u00a0"))
        ref=html(source["reference"]);height=measure(ref,x2-x0,8)+2
        if y+height>h-25:raise ValueError("Rujukan 5P tidak muat")
        spare,scale=page.insert_htmlbox(fitz.Rect(x0+5,y+2,x2-5,y+height+2),ref,css=css(8),scale_low=1)
        if spare<0 or scale!=1:raise ValueError("Rujukan 5P tidak dapat disahkan")
        return d.tobytes(garbage=4,deflate=True)
    finally:d.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--year",required=True,type=int,choices=COUNTS)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    year=a.year
    colors=[r for r in load(ROOT/"web/rph_login_canonical_layout_20261121.json")["subjects"] if r["subject_code"]=="SCIENCE"]
    if len(colors)!=1:
        raise ValueError("Science palette unavailable")
    c=colors[0]
    palette=Palette(c["strong"].lstrip("#"),c["tone"].lstrip("#"),c["tone"].lstrip("#"),"9AB2B7")
    rows=[(idx["lesson_id"],fixture(idx,r)) for idx,r in inputs(year)]
    from tools.audit_science_opening_5p_y2_y4_20261128 import records, prepare
    rows.extend((r["lesson_id"],prepare(r,p)) for r,p in records() if p.year==year)
    count=COUNTS[year]+{2:7,3:9,4:6}[year]
    if len(rows)!=count or len({cid for cid,_ in rows})!=count:
        raise ValueError("Incorrect combined inventory")
    issues=[]; passed=0
    heading=f"SAINS SK\nTAHUN {year}\n{DRAFT}"
    profile=dict.fromkeys(("class","date","time","students"),"")
    for cid,(s,companion,raw) in rows:
        try:
            path=a.out/(cid+".pdf")
            path.write_bytes(render_pdf(s,companion,raw,profile,palette,heading))
            inspect_pdf(path,[DRAFT,*MS_LABELS[5:],*[s[k] for k in FIELDS],*[companion["phases"][k] for k in PHASE_KEYS],s["reference"]])
            passed+=1
        except Exception as e:
            issues.append({"id":cid,"error":str(e)})
    report={"status":"INDEPENDENT_PDF_DRAFT_QA_ONLY","year":year,"total":count,"passed":passed,
            "academic_approved":False,"web_delivery_verified":False,"release":False,"issues":issues}
    (a.out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))
    return 1 if issues or passed!=count else 0

if __name__=="__main__":
    raise SystemExit(main())
