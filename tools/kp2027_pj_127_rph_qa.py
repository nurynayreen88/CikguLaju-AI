"""Offline QA only; no public routes or RPT/source replacement."""
from pathlib import Path
from hashlib import sha256
import json, argparse
from tools.kp2027_bmsjk_qa_word_pdf import render_docx, render_pdf

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"audits/kp2027_pj_t1_127_rph_structured_candidates_20261124.json"
COUNTS={"A":64,"B":63}
FIELDS={"1.1":"Konsep pergerakan","1.2":"Kemahiran lokomotor dan bukan lokomotor","1.3":"Pergerakan berirama","1.4":"Gimnastik asas","2.1":"Kemahiran manipulasi","3.1":"Rekreasi dan aktiviti luar","4.1":"Kecergasan","4.2":"Kecergasan fizikal"}
def records():
    data=json.loads(SOURCE.read_text(encoding="utf-8"))
    if data["status"]!="QA_NEW_SOURCE_NOT_PUBLISHED":
        raise ValueError("Unexpected release state")
    for group,count in COUNTS.items():
        items=data["groups"][group]
        assert [x["pdp"] for x in items]==list(range(1,count+1))
        assert len({s["code"] for x in items for s in x["standards"]})==167
        for r in items:
            assert r["group"]==group and r["status"]=="QA_NOT_READY"
            assert r["date"] is None and r["textbook"] is None
            assert len(r["activities"])==3
            assert {s["code"][0] for s in r["standards"]}=={"P","K","A"}
            yield r

def layout(r):
    h=("RANCANGAN PENGAJARAN HARIAN","PENDIDIKAN JASMANI • TAHUN 1",
       f"Kumpulan {r['group']} • PdP {r['pdp']:03d} • {r['title']}")
    # DK uses bidang/subbidang and P/K/A, not KSSR SK numbering.
    fields=[
        ("Bidang / Subbidang",[r["primary_sp"][1:].rsplit(".",1)[0]+" • "+FIELDS[r["primary_sp"][1:].rsplit(".",1)[0]]]),
        ("Standard Pembelajaran",[s["code"]+" "+s["text"] for s in r["standards"]]),
        ("Objektif Pembelajaran",[r["objective"]]),
        ("Kriteria Kejayaan",[r["criteria"]]),
        ("BBM",[r["bbm"]]),("Keselamatan",[r["safety"]]),
        ("EMK / Nilai",["Keselamatan, tanggungjawab dan hormat."]),
        ("PAK21",["Komunikasi dan pembelajaran kolaboratif."]),
    ]
    activities=[("Set Induksi",[("Guru",r["induction"])])]
    for i,a in enumerate(r["activities"],1):
        role="Murid" if a["body"].startswith("Murid") else "Guru"
        activities.append((f"Aktiviti {i}: {a['title']}",[(role,a["body"])]))
    activities.append(("Penutup",[("Murid",r["closure"])]))
    follow=[("PBD",[r["pbd"]]),("Pemulihan",[r["remedial"]]),
            ("Pengayaan",[r["extension"]]),("Refleksi",[r["reflection"]])]
    return h,(fields,activities,follow)

def render(r,fmt):
    fn={"docx":render_docx,"pdf":render_pdf}[fmt]
    return fn(r,layout=layout(r),tone="F3F2E8",strong="E9E7D4")

def export(out):
    import fitz
    from io import BytesIO
    from docx import Document
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    files=[]
    for r in records():
        for fmt in ("docx","pdf"):
            data=render(r,fmt)
            if fmt=="docx":
                doc=Document(BytesIO(data))
                assert len(doc.tables)==4
                text=" ".join(c.text for t in doc.tables for row in t.rows for c in row.cells)
                assert all(s["code"] in text and s["text"] in text for s in r["standards"])
                assert all(any(run.bold and run.text.startswith("Aktiviti "+str(i)) for t in doc.tables for row in t.rows for c in row.cells for p in c.paragraphs for run in p.runs) for i in (1,2,3))
            else:
                with fitz.open(stream=data,filetype="pdf") as pdf:
                    assert len(pdf)==1, (r["group"],r["pdp"],len(pdf))
                    text=" ".join(pdf[0].get_text().split())
                    assert all(s["code"] in text for s in r["standards"])
                    assert "Aktiviti 3" in text and "Refleksi" in text
                    assert abs(pdf[0].rect.width-595.28)<1 and abs(pdf[0].rect.height-841.89)<1
            name=f"CIKGULAJU_KP2027_PJ_T1_{r['group']}_PDP{r['pdp']:03d}_QA.{fmt}"
            (out/name).write_bytes(data)
            files.append({"file":name,"sha256":sha256(data).hexdigest(),"bytes":len(data)})
    assert len(files)==254
    (out/"manifest.json").write_text(json.dumps({"status":"QA_NOT_READY","ready":0,"files":files},indent=2),encoding="utf-8")
    print("Verified QA files:",len(files))
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out-dir",required=True)
    export(parser.parse_args().out_dir)
