"""QA real Math 5P renderer, not the production route."""
import json
import re
from pathlib import Path
from unicodedata import normalize
from hashlib import sha256
import fitz
from web import kp2027_math_5p as five
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"qa_math_5p"
def norm(s):return " ".join(re.sub(r"(?<=\w)-[ \t]*\r?\n[ \t]*(?=\w)","-",normalize("NFKC",s)).split())
def build():
    _,original,drafts,reviews=five.inventory()
    OUT.mkdir(exist_ok=True)
    native=OUT/"native"
    native.mkdir(exist_ok=True)
    manifest=[]
    errors=[]
    for g,n in sorted(drafts):
        name=f"DRAF_MATEMATIK_KP2027_T1_5P_{g}_{n:03d}"
        try:
            data,c,raw,profile=five.prepare(g,n,{})
            (OUT/(name+".docx")).write_bytes(five.render(g,n,"word",{}))
            pdf=five.render(g,n,"pdf",{})
            (native/(name+".pdf")).write_bytes(pdf)
            with fitz.open(stream=pdf,filetype="pdf") as d:
                assert len(d)==1
                txt=norm(d[0].get_text())
                for term in (data["sp"],data["objective"],data["criteria"],*c["phases"].values(),"Refleksi"):
                    assert norm(term) in txt, "Missing "+term
            manifest.append({"group":g,"lesson":n,"sp_code":drafts[g,n]["sp_code"],"filename":name,
                "original_word_sha256":original[g][str(n)]["word"],"original_pdf_sha256":original[g][str(n)]["pdf"],
                "source_sha256":sha256(raw).hexdigest(),"dk_scope_correction":bool(reviews[g,n].get("correction")),
                "source":data,"phases":c["phases"],"ready":False})
        except Exception as e:
            errors.append({"file":name,"error":str(e)})
    (OUT/"native-report.json").write_text(json.dumps({"total":249,"passed":len(manifest),"issues":errors},ensure_ascii=False,indent=2))
    (OUT/"manifest.json").write_text(json.dumps({"status":"DRAFT_QA_ONLY","records":manifest},ensure_ascii=False,indent=2))
    assert not errors, errors[:10]
    assert len(manifest)==249 and sum(x["dk_scope_correction"] for x in manifest)==40
    print("Generated and checked",len(manifest),"Word and native PDF drafts")
if __name__=="__main__":build()
