"""Optional Mathematics KP2027 RPH 5P; feature gated; source identities locked.
QA only until route and all document checks pass.
"""
import json
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from html import escape
from web.kp2027_math_canary_web import PilotUnavailable
from web.kp2027_pilot_teacher_fields import parse_teacher_fields
from web.rph_5p_v5_layout import MATH_V5, MS_LABELS, PHASE_KEYS, FIELDS, render_word, validate

PALETTE=MATH_V5
ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"audits"
def load(name):return json.loads((AUDIT/name).read_text(encoding="utf-8"))
SK={"1.1":"Nilai Nombor","1.2":"Ikatan Nombor",
    "2.1":"Tambah dalam Lingkungan 30","2.2":"Tolak dalam Lingkungan 30",
    "3.1":"Wang Kertas dan Duit Syiling","3.2":"Nilai Wang",
    "4.1":"Bentuk Dua Dimensi","5.1":"Masa dalam Sehari",
    "5.2":"Tarikh, Hari, Minggu, Bulan dan Tahun",
    "6.1":"Unit Bukan Piawai","6.2":"Unit Piawai","7.1":"Piktograf"}


@lru_cache(maxsize=1)
def inventory():
    source=load("rph_5p_math_kp2027_source_fields_20261127.json")["records"]
    original=json.loads((ROOT/"web/kp2027_math_v11_catalog.json").read_text())
    audit=load("rph_5p_math_kp2027_t1_individual_source_audit_20261127.json")
    companions=[]
    for i in range(1,4):
        companions.extend(load(f"rph_5p_math_kp2027_t1_batch{i:02d}_20261127.json")["records"])
    key=lambda x:(x["group"],x["lesson"])
    drafts={key(x):x for x in companions}
    reviews={key(x):x for x in audit["records"]}
    expected={(g,n) for g,count in (("A",125),("B",124)) for n in range(1,count+1)}
    assert len(companions)==len(reviews)==249 and set(drafts)==set(reviews)==expected
    assert len(source)==30
    return source,original,drafts,reviews

def prepare(g,n,payload):
    source,original,drafts,reviews=inventory()
    if (g,n) not in drafts:raise PilotUnavailable("PdP 5P tidak tersedia")
    row,review=drafts[g,n],reviews[g,n]
    code=row["sp_code"]
    cat=original[g][str(n)]
    assert cat["sp"]==code==review["sp_code"] and cat["word"]==row["source_word_sha256"] and cat["pdf"]==row["source_pdf_sha256"]
    fields=dict(source[code])
    # Normalize only the two known PDF extraction artifacts. Do not change math.
    if code=="2.2.1":
        fields["bbm"]=fields["bbm"].replace("kad simbol dan =, kad gambar.−","kad simbol − dan =, kad gambar.")
    if code=="2.2.2":
        fields["pbd"]="Lima item: 8 − 3, 9 − 5, 18 − 5, 24 − 7 dan 21 − 6; guru catat strategi dan ketepatan."
    correction=review.get("correction")
    phases=dict(correction["phases"] if correction else row["phases"])
    if correction:
        for k in ("objective","criteria","bbm","pbd","closure","remedial","extension"):
            fields[k]=correction[k]
    # Preserve quantitative criteria and source PBD. The correction's proposed
    # assessment may repeat the criteria; keep the shorter explicit PBD instead.
    phases["evaluation"]=fields["pbd"]
    sk_code=code.rsplit(".",1)[0]
    data={
        "subject":"MATEMATIK_SK","year":1,"lesson_id":f"{g}-{n:03d}","curriculum":"KP2027",
        "topic":fields["sk"]+" / "+fields["topic"],
        "sk":sk_code+" "+SK[sk_code],"sp":fields["sp"],
        "objective":fields["objective"],"criteria":fields["criteria"],
        "closure":fields["closure"].removesuffix(" Tindakan pemulihan dan pengayaan dilaksanakan mengikut keperluan."),
        "aids_pak21_emk":"BBM: "+fields["bbm"]+"\nPAK21 / KBAT: "+fields["pak"]+"\nEMK / Nilai: "+fields["emk"],
        "remedial_enrichment":"Pemulihan: "+fields["remedial"]+"\nPengayaan: "+fields["extension"],
        "reflection":"Kriteria: "+fields["criteria"]+"\nBilangan murid menguasai:    Belum menguasai:\nTindakan susulan:",
        "reference":"Rujukan: DK Matematik Tahun 1 (BPK, 2026) • RPT 2027.",
    }
    raw=json.dumps(data,sort_keys=True,ensure_ascii=False).encode()
    companion={**{k:data[k] for k in ("subject","year","lesson_id","curriculum")},
                "source_sha256":sha256(raw).hexdigest(),"phases":phases}
    fields_teacher=parse_teacher_fields(payload)
    if fields_teacher["_reflection_mode"]=="manual":
        data["reflection"]=fields_teacher["_reflection"]
    else:
        data["reflection"]="Kriteria: "+fields["criteria"]+"\nBilangan murid menguasai:    Belum menguasai:\nTindakan susulan: "+fields["remedial"]
    raw=json.dumps(data,sort_keys=True,ensure_ascii=False).encode()
    companion["source_sha256"]=sha256(raw).hexdigest()
    validate(data,companion,source_bytes=raw)
    profile=dict(zip(("class","date","time","students"),(fields_teacher[k] for k in ("Kelas:","Tarikh:","Masa:","Bil. Murid:"))))
    return data,companion,raw,profile

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
        if more:raise PilotUnavailable("Ruang 5P tidak muat")
        return box[3]-box[1]+2
    def cell(page,l,t,r,b,v,size,fill=None,center=False):
        page.draw_rect(fitz.Rect(l,t,r,b),color=border,fill=fills.get(fill,(1,1,1)),width=.55)
        mh=measure(v,r-l,size,center)
        y=t+(b-t-mh)/2
        spare,scale=page.insert_htmlbox(fitz.Rect(l+5,y,r-5,y+mh),v,css=css(size,center),scale_low=1)
        if spare<0 or scale!=1:raise PilotUnavailable("Teks 5P tidak muat")
    d=fitz.open()
    try:
        page=d.new_page(width=w,height=h);y=36
        def row(left,right,*,fill="label",rightfill=None,size=9):
            nonlocal y
            height=max(measure(left,x1-x0,size),measure(right,x2-x1,size))+5
            if y+height>h-36:raise PilotUnavailable("RPH 5P tidak muat satu A4")
            cell(page,x0,y,x1,y+height,left,size,fill)
            cell(page,x1,y,x2,y+height,right,size,rightfill)
            y+=height
        title=html(labels[0],True);height=measure(title,x2-x0,14,True)+7
        cell(page,x0,y,x2,y+height,title,14,"title",True);y+=height
        info="\n".join(f"{label}: {profile[key]}".rstrip() for label,key in zip(labels[1:5],("class","date","time","students")))
        row(html(info,True),html("MATEMATIK SK\nTAHUN 1",True),fill="header",rightfill="header")
        for i,key in enumerate(FIELDS[:5],5):
            row(html(labels[i],True),html(source[key]))
        steps=[]
        for i,key in enumerate(PHASE_KEYS):
            steps.extend([(html(labels[11+i],True),"label"),(html(c["phases"][key]),None)])
        heights=[measure(v,x2-x1,9)+5 for v,_ in steps]
        total=sum(heights)
        if y+total>h-36:raise PilotUnavailable("Aktiviti 5P tidak muat")
        cell(page,x0,y,x1,y+total,html(labels[10],True),9,"label",True)
        for (value,fill),height in zip(steps,heights):
            cell(page,x1,y,x2,y+height,value,9,fill);y+=height
        for i,key in enumerate(FIELDS[5:],16):
            row(html(labels[i],True),html(source[key]))
        ref=html(source["reference"]);height=measure(ref,x2-x0,8)+2
        if y+height>h-25:raise PilotUnavailable("Rujukan 5P tidak muat")
        page.insert_htmlbox(fitz.Rect(x0+5,y+2,x2-5,y+height+2),ref,css=css(8),scale_low=1)
        return d.tobytes(garbage=4,deflate=True)
    finally:d.close()

def render(g,n,fmt,fields):
    data,c,raw,profile=prepare(g,n,fields)
    if fmt=="word":
        return render_word(data,c,source_bytes=raw,palette=PALETTE,subject_heading="MATEMATIK SK\nTAHUN 1",profile=profile)
    if fmt=="pdf":return render_pdf(data,c,profile)
    raise PilotUnavailable("Format tidak sah")
