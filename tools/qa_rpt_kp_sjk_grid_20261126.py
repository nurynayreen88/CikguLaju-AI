"""Private rendering QA of the 21 currently available exact KP/SJK sources."""
import tempfile,subprocess,json,re
from pathlib import Path
from io import BytesIO
import fitz
from docx import Document
from web.rpt_2027_all_http import SCHOOL_RPTS
from web import kp2027_year1_rpt_combined as kp
from tools.rpt_existing_table_grid_20261126 import polish
def sources():
    for subject in kp.SUBJECTS:
        yield f"kp:{subject}",subject,kp.document(subject,"docx")[0],kp.document(subject,"pdf")[0]
    for school,subjects in SCHOOL_RPTS.items():
        for slug,module in subjects.items():
            for y in module.YEARS:
                word=module.document_path(y,"docx");pdf=module.document_path(y,"pdf")
                if word and pdf:yield f"{school}:{slug}:{y}",slug,word.read_bytes(),pdf.read_bytes()
def run(group):
    items=[v for v in sources() if v[0].split(":")[0]==group]
    for key,subject,word,pdf in items:
        revised,targets=polish(word,subject)
        d=Document(BytesIO(revised))
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td);p=folder/"sample.docx";p.write_bytes(revised)
            subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),"--headless","--convert-to","pdf","--outdir",td,str(p)],check=True,timeout=240)
            with fitz.open(folder/"sample.pdf") as actual,fitz.open(stream=pdf,filetype="pdf") as original:
                assert len(actual)>1
                # Source cover is retained when publishing PDF; do not replace it with Word conversion.
                assert all(page.get_text().strip() for page in list(actual)[1:])
                print("PASS",json.dumps({"key":key,"teaching_tables":len(targets),"rows":sum(len(d.tables[i].rows)-1 for i in targets),"pages_original":len(original),"pages_rendered":len(actual),"untouched_non_teaching_tables":len(d.tables)-len(targets)},ensure_ascii=False),flush=True)
if __name__=="__main__":
    import sys
    run(sys.argv[1])
