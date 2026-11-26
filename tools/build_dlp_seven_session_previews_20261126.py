"""Private fixed-session RPT preview, retaining source CS/LS and references.

Not a release: source evidence is displayed for review, not claimed to be a
finished split/combined RPH. The published manifest and RPH catalogue are untouched.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from datetime import date
from io import BytesIO
import argparse,json,re,subprocess
import fitz
from docx import Document
from tools.audit_dlp_seven_fixed_sessions_20261126 import SETS,plan
from tools.build_rpt_dlp_native_20261126 import ROOT,extract,document_path
from tools.build_rpt_dlp_full_standards_20261126 import build_word,HEADS
from tools.build_kssr_rpt_merged_week_batch_20261126 import norm
from tools.rpt_dlp_compact_pagination_20261126 import measure_weeks,choose_sizes
from tools.prepare_dlp_week_column_release_20261126 import verify_bottom

def candidate_rows(subject,year):
    key=f"{subject}:{year}";p=plan(subject,year)
    with fitz.open(document_path(subject,year,root=ROOT/"dlp")) as pdf:source=extract(pdf)
    mappings=json.loads((ROOT/"dlp/standard_descriptions/review_mappings.json").read_text())["mappings"].get(key,{})
    lookup={};review=0
    for c,links in source:
        m=re.match(r"Lesson\s+(\d+)\b",c[1][0])
        if m:label=f"L{int(m[1]):02d}"
        else:review+=1;label=f"R{review:02d}"
        field=c[2]
        if " ".join(field) in ("Consolidation Review taught standards","Review Review taught standards"):
            codes=mappings.get(label);assert codes,(key,label)
            field=["LS "+", ".join(codes)]
        lookup[label]=(c,links,field)
    def span(g):
        a,b=map(date.fromisoformat,(g["start"],g["end"]))
        return f"{a.day}-{b.day} {b:%b}" if a.month==b.month else f"{a.day} {a:%b}-{b.day} {b:%b}"
    result=[];loads={};previous=None
    for w in p["weeks"]:
        n=w["week"];a,b=w["dates"]
        date_label=[f"Week {n:02d}","A "+span(a),"B "+span(b)]
        loads[n]=sum(s["minutes"] for s in w["sessions"])
        for i,s in enumerate(w["sessions"],1):
            title=[f"Session {i}"];fields=[];evidence=[];reference=[];urls=[]
            parts=s["source_parts"]
            if not parts:
                # No new standard or numbered RPH is invented for reserve slots.
                # Before teaching starts, a reserve is diagnostic using next source.
                label=previous or next(iter(lookup))
                c,links,field=lookup[label]
                title.append(f"Reserve / PBD — reference {label}")
                fields.extend(field)
                evidence.extend(["Candidate follow-up; activity requires review. Source evidence:",*c[3]])
                reference.extend(c[4]);urls.extend(links)
            else:
                for part in parts:
                    label=part["source_id"];previous=label
                    c,links,field=lookup[label]
                    full=(part["from_minute"]==0 and part["to_minute"]==part["original_minutes"])
                    role="" if full else f" (part {part['from_minute']//60+1}, continuation reference)"
                    # Keep original lesson and unit wording; no replacement IDs.
                    title.append(f"{label}{role}: "+" ".join(c[1]))
                    fields.extend(field)
                    evidence.extend([f"{label} source evidence:",*c[3]])
                    reference.extend(c[4]);urls.extend(links)
                if s["status"]!="EXACT_SOURCE_SLOT_VERIFY_RPH":
                    evidence.append("Candidate session — activity scope requires review.")
            # No internal duration is printed in the public-style document.
            reference=[v for v in reference if not re.fullmatch(r"\d+\s*min(?:utes)?",v.strip(),re.I)]
            result.append(([date_label,title,fields,evidence,list(dict.fromkeys(reference))],list(dict.fromkeys(urls))))
    assert len(result)==p["sessions"]
    return result,loads,p

def convert(word,folder):
    subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),"--headless","--convert-to","pdf","--outdir",str(folder),str(word.resolve())],check=True,timeout=180)
    return folder/(word.stem+".pdf")

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--subject",required=True);parser.add_argument("--year",type=int,required=True);parser.add_argument("--out",type=Path,required=True);args=parser.parse_args()
    subject,year=args.subject,args.year
    assert (subject,year) in SETS
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    key=f"{subject}:{year}";rows,loads,p=candidate_rows(subject,year)
    with TemporaryDirectory() as temp,patch("tools.dlp_whole_lesson_calendar_20261126.schedule",return_value=(rows,loads)):
        folder=Path(temp)
        blob,*_=build_word(subject,year,whole_weeks=True,pilot=True)
        pilot=folder/"pilot.docx";pilot.write_bytes(blob)
        with fitz.open(convert(pilot,folder)) as pdf:heights=measure_weeks(pdf)
        assert len(heights)==35,(key,len(heights))
        sizes=choose_sizes(heights)
        blob,cover,used,expected,_=build_word(subject,year,whole_weeks=True,compact_sizes=sizes)
        assert used==rows
        stem=f"QA_RPT_{subject}_Year_{year}_2027"
        word=out/(stem+".docx");word.write_bytes(blob)
        doc=Document(BytesIO(blob))
        assert len(doc.tables)==len(sizes)+1
        header=[*HEADS[:-1],"Textbook"]
        assert all([c.text for c in t.rows[0].cells]==header for t in doc.tables[:-1])
        assert sum(len(t.rows)-1 for t in doc.tables[:-1])==len(rows)
        raw=convert(word,folder)
        target=out/(stem+".pdf")
        with fitz.open(raw) as gen,fitz.open(stream=cover,filetype="pdf") as front,fitz.open() as merged:
            merged.insert_pdf(front,from_page=0,to_page=0);merged.insert_pdf(gen,from_page=1)
            merged.save(target,garbage=4,deflate=True)
        with fitz.open(target) as pdf:
            assert len(pdf)==len(sizes)+2,(key,len(pdf),sizes)
            with fitz.open(ROOT/"full_standards_dlp_pdf_2027"/subject/f"tahun_{year}.pdf") as old:
                assert pdf[0].get_pixmap().samples==old[0].get_pixmap().samples,key
            for page,n in zip(list(pdf)[1:-1],sizes,strict=True):
                verify_bottom(page,key)
                text=norm(page.get_text())
                assert all(norm(h) in text for h in header)
                assert len(re.findall(r"(?m)^Week\s+\d{2}\s*$",page.get_text()))==n
            assert "Main school breaks" in pdf[-1].get_text()
        print("PRIVATE_RPT_PREVIEW_OK",key,"sessions",len(rows),"pages",len(sizes)+2,flush=True)
    (out/"session_review.json").write_text(json.dumps(p,indent=2)+"\n")

if __name__=="__main__":main()
