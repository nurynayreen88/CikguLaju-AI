"""Render real native RPH candidate documents using the pinned main engine.

Private QA only. All original teaching activities are preserved; no draft
is inserted into the live catalogue. Resolve full standards via the same
reviewed bank used by RPT. Missing session boundaries and duration review
are reported rather than concealed.
"""
from collections import Counter
from io import BytesIO
from pathlib import Path
import argparse,json,re,sys
from unittest.mock import patch
from reportlab.lib.styles import ParagraphStyle
sys.path.insert(0,str(Path.cwd()))
from web.rph_document_style import pdf_box_style
from docx import Document
import fitz
from dlp_year2_rph import year3_science_catalog,science_class_fields
from staging.dlp.year2.downloads import BY_SUBJECT
from staging.dlp.year6 import render_science
from web.rph_unified_engine import render_structured_rph

def source_records(year,subject='science_dlp'):
    if subject=='mathematics_dlp':
        from staging.dlp.year3 import render_mathematics as m3
        from staging.dlp.year4 import render_mathematics as m4
        from staging.dlp.year5 import render_mathematics as m5
        from staging.dlp.year6 import render_mathematics as m6
        if year==3:
            rows=[{'id':i,'title':t,'unit':u,'label':l,'materials':d['Materials']} for i,t,u,l,_,_,d,_ in m3.verify_drafts()]
        elif year==4:
            rows=[{'id':i,'title':t,'unit':u,'label':l,'materials':d['Materials']} for i,t,u,l,d,_ in m4.verify_drafts()]
        else:rows=(m5 if year==5 else m6).load_plans()[1]
    elif year==2:rows=[p for u in BY_SUBJECT['SCIENCE_DLP'].units for p in u['lessons']]
    elif year==3:rows=[p for u in year3_science_catalog() for p in u['lessons']]
    else:rows=render_science.load_plans()[1]
    output={}
    for p in rows:
        ident=p['id'];label=p.get('numbered_label') or p['label']
        m=re.search(r'\b(Lesson|Review)\s+(\d+)\b',label,re.I)
        assert m,(ident,label)
        name=m[1][0].upper()+f'{int(m[2]):02d}'
        assert name not in output
        output[name]=p
    return output

def _old_science_records(year):
    if year==2:rows=[p for u in BY_SUBJECT["SCIENCE_DLP"].units for p in u["lessons"]]
    elif year==3:rows=[p for u in year3_science_catalog() for p in u["lessons"]]
    else:rows=render_science.load_plans()[1]
    output={}
    for p in rows:
        ident=p["id"];label=p.get("numbered_label") or p["label"]
        m=re.search(r"\b(Lesson|Review)\s+(\d+)\b",label,re.I)
        assert m,(ident,label)
        name=m[1][0].upper()+f"{int(m[2]):02d}"
        assert name not in output
        output[name]=p
    return output

def unique(items):
    return list(dict.fromkeys(x for x in items if x))

def normal(value):
    if isinstance(value,(list,tuple)):return " · ".join(map(str,value))
    return str(value or "")

def full_standards(lines,bank):
    joined=" ".join(lines)
    joined=re.sub(r"\((?:Observe|Classify|Measure and use numbers|Communicate)\)","",joined,flags=re.I)
    current=None;parent=None;cs=[];ls=[]
    for m in re.finditer(r"\bCS\b|\bLS\b|(?<![\d.])\d+\.\d+(?:\.\d+)?(?:\([ivx]+\))?|\([ivx]+\)",joined,re.I):
        item=m.group()
        if item.upper() in ("CS","LS"):current=item.lower();parent=None;continue
        if not current:raise ValueError(joined)
        if item.startswith("("):item=parent+item
        else:parent=item.split("(")[0]
        text=bank.get("parts",{}).get(item) if "(" in item else bank[current].get(item)
        assert text,(current,item)
        (cs if current=="cs" else ls).append(item+" "+text)
    if not cs:
        for item in ls:
            code=item.split()[0].split("(")[0].rsplit(".",1)[0]
            cs.append(code+" "+bank["cs"][code])
    assert cs and ls,joined
    return unique(cs),unique(ls)

def compact_pdf(heading,details,rows,footer,teacher,*,padding_limit=2,leading=10.25):
    """Isolated layout trial: keep 9.5pt font and all content; reduce gaps only."""
    def style(name,*args,**kwargs):
        if name=="DLP body":kwargs["leading"]=leading
        return ParagraphStyle(name,*args,**kwargs)
    def box(padding):
        return pdf_box_style(min(padding,padding_limit))
    with patch("reportlab.lib.styles.ParagraphStyle",side_effect=style),patch("web.rph_document_style.pdf_box_style",side_effect=box):
        return render_structured_rph(source="dlp",fmt="pdf",heading=heading,details=details,activities=rows,footer=footer,teacher=teacher,compact=True)

def main():
    a=argparse.ArgumentParser();a.add_argument("--paired",type=Path,required=True);a.add_argument("--rpt-root",type=Path,required=True);a.add_argument("--year",type=int,choices=(2,3,4,5,6),required=True);a.add_argument("--subject",choices=("science_dlp","mathematics_dlp"),default="science_dlp");a.add_argument("--out",type=Path,required=True);args=a.parse_args()
    y=args.year;subject=args.subject;key=f"{subject}:{y}";math=subject=="mathematics_dlp"
    assert y in ((3,4,5,6) if math else (2,3,6))
    data=next(x for x in json.loads(args.paired.read_text())["sets"] if x["key"]==key)
    source=source_records(y,subject)
    bank=json.loads((args.rpt_root/"dlp/standard_descriptions"/f"{subject.split('_')[0]}_year{y}.json").read_text())
    reviews=json.loads((args.rpt_root/"dlp/standard_descriptions/review_mappings.json").read_text())["mappings"].get(key,{})
    out=args.out;out.mkdir(parents=True,exist_ok=True)
    counts=Counter();issues=[]
    for s in data["sessions"]:
        n=s["session"];labels=s["source_labels"];records=[source[l] for l in labels]
        activities=s["activities"];assert activities
        if "induction" not in activities[0]["phase"].lower() or "closure" not in activities[-1]["phase"].lower():
            issues.append({"session":n,"error":"missing authored boundary"});continue
        try:
            cs=[];ls=[]
            for label,field in zip(labels,s["standards"],strict=True):
                if " ".join(field) in ("Consolidation Review taught standards","Review Review taught standards"):
                    field=["LS "+", ".join(reviews[label])]
                c,l=full_standards(field,bank);cs.extend(c);ls.extend(l)
            # Use actual source materials, not an invented list.
            materials=unique([normal(p.get("materials")) for p in records])
            assert materials,(key,n)
            title=" / ".join(unique([normal(p.get("title")) for p in records]))
            unit=" / ".join(unique([normal(p.get("unit_title") or p.get("unit")) for p in records]))
            assert title and unit
            start="08:00";end="08:30" if s["slot_minutes"]==30 else "09:00"
            teacher={"class":f"{y} Bestari","date":"2027-01-12","time":f"{start} - {end}","students":"30"}
            heading=("Daily Lesson Plan",f"{'Mathematics' if math else 'Science'} (DLP) · Year {y} SK",title)
            details=[("Unit",unit),("Lesson / PdP"," / ".join(labels)),*science_class_fields(teacher,english=True),("Content Standards","\n".join(unique(cs))),("Learning Standards","\n".join(unique(ls))),("Book reference"," · ".join(s["references"])),("Learning objective","\n".join(s["objective"])),("Materials","; ".join(materials))]
            rows=[("Phase","Teacher","Pupils"),*[(p["phase"],p["teacher"],p["pupils"]) for p in activities]]
            footer=[("Reflection","___ of ___ pupils met the learning objective(s). Follow-up: ____________________.")]
            for fmt in ("word","pdf"):
                blob=render_structured_rph(source="dlp",fmt=fmt,heading=heading,details=details,activities=rows,footer=footer,teacher=teacher,compact=True,mathematics=math)
                if fmt=="word":
                    doc=Document(BytesIO(blob));assert len(doc.tables)==4
                    text=" ".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
                    for p in activities:
                        assert " ".join(p["pupils"].split()) in " ".join(text.split())
                    suffix="docx"
                else:
                    with fitz.open(stream=blob,filetype="pdf") as pdf:
                        old_pages=len(pdf);old_text="".join(pdf[i].get_text() for i in range(len(pdf)))
                    if old_pages>1 and y==2 and not math:
                        # Keep the proven compact layout for the other sessions.
                        # Try progressively smaller cell padding for session 7 only.
                        for padding_limit,leading in ((2,10.25),(1.5,10.25),(1,10.0),(0.75,9.8)):
                            blob=compact_pdf(heading,details,rows,footer,teacher,padding_limit=padding_limit,leading=leading)
                            with fitz.open(stream=blob,filetype="pdf") as trial:
                                if len(trial)==1:break
                            if n!=7:break
                        with fitz.open(stream=blob,filetype="pdf") as pdf:
                            new_text="".join(page.get_text() for page in pdf)
                            # ReportLab repeats the activity table header on a
                            # continuation page. Only allow removal of that exact
                            # redundant header, never lesson or reflection text.
                            normalize=lambda t:re.sub(r"\s+","",t)
                            old_chars=Counter(normalize(old_text));new_chars=Counter(normalize(new_text))
                            removed=old_chars-new_chars;added=new_chars-old_chars
                            from dlp_year2_rph import _activity_table
                            repeated_header=Counter(normalize("".join(_activity_table(rows,english=True)[0])))
                            allowed=Counter({ch:count*(old_pages-1) for ch,count in repeated_header.items()})
                            assert not added and (not removed or removed==allowed),("layout changed text",n,dict(removed),dict(added))
                            # Every teacher/pupil task and each nonempty details
                            # value must independently survive text extraction.
                            flat=normalize(new_text)
                            for value in [p["teacher"] for p in activities]+[p["pupils"] for p in activities]+[v for _,v in details]+[v for _,v in footer]:
                                assert normalize(str(value)) in flat,("missing compact field",n,str(value)[:100])
                            assert len(pdf)==1,("compact PDF page count",len(pdf))
                            assert all(span["size"]>=9.4 for page in pdf for block in page.get_text("dict")["blocks"] for line in block.get("lines",[]) for span in line["spans"] if span["text"].strip()),("unexpected font shrink",n)
                        counts["compact_spacing_fix"]+=1
                    with fitz.open(stream=blob,filetype="pdf") as pdf:
                        assert len(pdf)==1,("PDF page count",len(pdf))
                    suffix="pdf"
                (out/f"QA_{'MAT' if math else 'SCI'}_Y{y}_SESSION_{n:03d}.{suffix}").write_bytes(blob)
                counts[fmt]+=1
        except Exception as e:
            issues.append({"session":n,"error":str(e)})
    result={"key":key,"sessions":len(data["sessions"]),"rendered":dict(counts),"issues":issues,"release_ready":False}
    (out/"qa-report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("DLP_NATIVE_SESSION_QA",json.dumps(result,ensure_ascii=False),flush=True)

if __name__=="__main__":main()
