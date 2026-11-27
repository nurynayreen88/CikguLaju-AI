"""Owner-authorized optional BM SK KP2027 5P, pending document QA.
No textbook yet: DK + existing RPT/lesson source remain authoritative.
No account, quota, or original RPH mutations here.
"""
import json
from hashlib import sha256
from functools import lru_cache
from pathlib import Path
from html import escape
from web import kp2027_bm_rpt_aligned as bm
from web.kp2027_pilot_teacher_fields import parse_teacher_fields
from web.rph_5p_v5_layout import Palette, MS_LABELS, PHASE_KEYS, FIELDS, render_word, validate

PALETTE=Palette("DBE8F5","F4F7FA","EDF3FA","BAC7D0")
PAGES={"1.1":22,"1.2":23,"2.1":30,"2.2":31,"2.3":31,"3.1":38,"3.2":39,"4.1":44,"4.2":44}
ROOT=Path(__file__).resolve().parents[1]
@lru_cache(maxsize=1)
def companions():
    raw=bm.approved_source()
    result={}
    for i in range(1,6):
        doc=json.loads((ROOT/"audits"/f"rph_5p_source_adaptation_bm_t1_batch{i:02d}_20261127.json").read_text())
        for c in doc["records"]:
            g,n=c["group"],c["lesson"]
            r=raw[g][str(n)]
            if (g,n) in result or c.get("source_record",r)!=r or c.get("sp_code",r["sp_code"])!=r["sp_code"]:
                raise bm.Unavailable("Sumber 5P tidak sepadan")
            if set(c["phases"])!=set(PHASE_KEYS) or len(set(c["phases"].values()))!=5:
                raise bm.Unavailable("Fasa 5P tidak lengkap")
            result[g,n]=c["phases"]
    if set(result)!={(g,n) for g,count in bm.COUNTS.items() for n in range(1,count+1)}:
        raise bm.Unavailable("Inventori 5P belum lengkap")
    return result

def prepare(g,n,payload):
    r=bm.lesson(g,n)
    fields=parse_teacher_fields(payload)
    page=PAGES[r["sk_code"]]
    if r["sp_code"] in ("1.2.3","1.2.4"):page=24
    if r["sp_code"] in ("2.3.2","2.3.3"):page=32
    source={
        "subject":"BM_SK","year":1,"lesson_id":f"{g}-{n:03d}","curriculum":"KP2027",
        "topic":r["unit"]+" / "+r["title"],"sk":r["sk_code"]+" "+r["sk"],
        "sp":r["sp_code"]+" "+r["sp"],"objective":r["objective"],"criteria":r["criteria"],
        "closure":r["closure"],
        "aids_pak21_emk":r["material"]+"\nPAK21 / KBAT: Kolaborasi, komunikasi, pemikiran kritis; menerangkan sebab dan membuat pilihan yang bersesuaian.\nEMK / Nilai: Bahasa; komunikasi berhemah; kerjasama; hormat-menghormati; tanggungjawab.",
        "remedial_enrichment":"Pemulihan: "+r["remedial"]+"\nPengayaan: "+r["extension"],
        "reflection":bm._reflection(r,fields),
        "reference":f"Rujukan: DK BM SK Tahun 1 (BPK, 2026), hlm. {page}."
    }
    raw=json.dumps(source,ensure_ascii=False,sort_keys=True).encode()
    c={**{k:source[k] for k in ("subject","year","lesson_id","curriculum")},
       "source_sha256":sha256(raw).hexdigest(),"phases":companions()[g,n]}
    validate(source,c,source_bytes=raw)
    profile=dict(zip(("class","date","time","students"),(fields[k] for k in ("Kelas:","Tarikh:","Masa:","Bil. Murid:"))))
    return source,c,raw,profile

def render_pdf(source,c,profile):
    """Native one-page PDF; no external process, no truncation or scaling."""
    import fitz
    labels=MS_LABELS
    w,h=595.28,841.89
    x0,x1,x2=42.52,161.58,552.76
    def rgb(hexstr):return tuple(int(hexstr[i:i+2],16)/255 for i in (0,2,4))
    border=rgb(PALETTE.border)
    fills={k:rgb(getattr(PALETTE,k)) for k in ("title","header","label")}
    def html(v,b=False):
        s=escape(str(v),quote=False).replace("\n","<br/>")
        return "<b>"+s+"</b>" if b else s
    def css(size,center=False):
        return f"body{{font-family:sans-serif;font-size:{size}pt;line-height:1.13;margin:0;padding:0;color:#17232b;"+("text-align:center;" if center else "")+"}p{margin:0;padding:0;}"
    def measure(v,width,size,center=False):
        more,box=fitz.Story(v,user_css=css(size,center)).place(fitz.Rect(0,0,width-10,780))
        if more:raise bm.Unavailable("Ruang 5P tidak muat")
        return box[3]-box[1]+2
    def cell(page,l,t,r,b,v,size,fill=None,center=False):
        page.draw_rect(fitz.Rect(l,t,r,b),color=border,fill=fills.get(fill,(1,1,1)),width=.55)
        mh=measure(v,r-l,size,center)
        y=t+(b-t-mh)/2
        spare,scale=page.insert_htmlbox(fitz.Rect(l+5,y,r-5,y+mh),v,css=css(size,center),scale_low=1)
        if spare<0 or scale!=1:raise bm.Unavailable("Teks 5P tidak muat")
    d=fitz.open()
    try:
        page=d.new_page(width=w,height=h);y=36
        def row(left,right,*,fill="label",rightfill=None,size=9):
            nonlocal y
            height=max(measure(left,x1-x0,size),measure(right,x2-x1,size))+5
            if y+height>h-36:raise bm.Unavailable("RPH 5P tidak muat satu A4")
            cell(page,x0,y,x1,y+height,left,size,fill)
            cell(page,x1,y,x2,y+height,right,size,rightfill)
            y+=height
        title=html(labels[0],True);height=measure(title,x2-x0,14,True)+7
        cell(page,x0,y,x2,y+height,title,14,"title",True);y+=height
        info="\n".join(f"{label}: {profile[key]}".rstrip() for label,key in zip(labels[1:5],("class","date","time","students")))
        row(html(info,True),html("BAHASA MELAYU SK\nTAHUN 1",True),fill="header",rightfill="header")
        for i,key in enumerate(FIELDS[:5],5):
            row(html(labels[i],True),html(source[key]))
        steps=[]
        for i,key in enumerate(PHASE_KEYS):
            steps.extend([(html(labels[11+i],True),"label"),(html(c["phases"][key]),None)])
        heights=[measure(v,x2-x1,9)+5 for v,_ in steps]
        total=sum(heights)
        if y+total>h-36:raise bm.Unavailable("Aktiviti 5P tidak muat")
        cell(page,x0,y,x1,y+total,html(labels[10],True),9,"label",True)
        for (value,fill),height in zip(steps,heights):
            cell(page,x1,y,x2,y+height,value,9,fill);y+=height
        for i,key in enumerate(FIELDS[5:],16):
            row(html(labels[i],True),html(source[key]))
        ref=html(source["reference"]);height=measure(ref,x2-x0,8)+2
        if y+height>h-25:raise bm.Unavailable("Rujukan 5P tidak muat")
        page.insert_htmlbox(fitz.Rect(x0+5,y+2,x2-5,y+height+2),ref,css=css(8),scale_low=1)
        return d.tobytes(garbage=4,deflate=True)
    finally:d.close()

def render(g,n,fmt,fields):
    source,c,raw,profile=prepare(g,n,fields)
    if fmt=="word":
        return render_word(source,c,source_bytes=raw,palette=PALETTE,subject_heading="BAHASA MELAYU SK\nTAHUN 1",profile=profile)
    if fmt=="pdf":return render_pdf(source,c,profile)
    raise bm.Unavailable("Format tidak sah")
