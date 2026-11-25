"""Generate five PI RPT review PDFs from the exact final native source and calendar.
No production PDF replacement or account access. Fixed durations never printed.
"""
from pathlib import Path
import json
import re
import fitz
from tools.pi_rpt_reference_layout_20261125 import build_preview
from web.pi_rph_no_duration_display_20261125 import display_topic

ROOT=Path("qa/pi-rpt-final-source")
UNITS={"Al-Quran":"القرءان","Hadis":"حديث","Akidah":"عقيدة","Ibadah":"عبادة","Sirah":"سيره","Adab":"ادب","Jawi":"جاوي"}
COUNTS={2:112,3:148,4:152,5:144,6:142}

def main():
    source=json.loads((ROOT/"records.json").read_text(encoding="utf8"))
    calendar=json.loads((ROOT/"teacher_schedule.json").read_text(encoding="utf8"))
    assert source["source_commit"]==calendar["source_commit"]
    for year,total in COUNTS.items():
        records=[r for r in source["records"] if r["year"]==year]
        schedule=calendar["years"][str(year)]["weeks"]
        index={n:(w,data["dates"]) for w,data in schedule.items() for n in data["pdp"]}
        assert set(index)==set(range(1,total+1))
        rows=[]
        for r in records:
            n=r["pdp"]
            w,dates=index[n]
            topic=display_topic(r.get("topic") or "")
            sub=display_topic(r.get("subtopic") or "")
            if sub and sub not in topic:
                topic=" / ".join(x for x in (topic,sub) if x)
            note=r["objective"]+"\n"+"\n".join(title for title,body in r["activities"])
            rows.append({"id":f"{n:03d}","week":f"M{int(w):02d}","a_start":dates[0],"a_end":dates[1],"b_start":dates[2],"b_end":dates[3],"unit":UNITS.get(r["unit"],r["unit"]),"topic":topic,"sk":str(r["sk"] or "—"),"sp":str(r["sp"] or "—").replace("RPT ٢٠٢٦","RPT ٢٠٢٧"),"note":note})
        path=ROOT/f"RPT_Pendidikan_Islam_Tahun_{year}_2027_preview.pdf"
        build_preview("pendidikan_islam",year,rows,path,max_span_rows=2,first_week_span_rows=2)
        with fitz.open(path) as pdf:
            assert len(pdf)>1
            assert all(abs(p.rect.width-841.9)<2 and abs(p.rect.height-595.3)<2 for p in pdf)
            printed=[int(x) for p in list(pdf)[1:] for x in re.findall(r"PdP (\d{3})",p.get_text())]
            assert printed==list(range(1,total+1)),(year,len(printed),printed[:10])
            for page in [0,1,len(pdf)-1]:
                pdf[page].get_pixmap(matrix=fitz.Matrix(1.3,1.3),alpha=False).save(str(ROOT/f"PI_T{year}_page{page+1}.png"))
            print("PI_RPT_PREVIEW",year,total,len(pdf),flush=True)

if __name__=="__main__":
    main()
