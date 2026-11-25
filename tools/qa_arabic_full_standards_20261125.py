"""Offline SK/SP candidate QA. Never promotes or calls production endpoints."""
import csv
import json
from pathlib import Path
from docx import Document
from tools.arabic_178_draft_shared_layout_20261124 import ROOT, BANK, INDEX, COUNTS, render

def main():
    out = Path("qa-arabic-full-standards")
    out.mkdir(exist_ok=True)
    sk4 = json.loads((ROOT/"audits/arabic_draft_y4_sk_visual_candidates_20261125.json").read_text(encoding="utf-8"))
    sk56 = json.loads((ROOT/"audits/arabic_draft_y5_y6_sk_text_candidates_20261125.json").read_text(encoding="utf-8"))
    bank = json.loads(BANK.read_text(encoding="utf-8"))["years"]
    candidates = {"4": sk4["entries"], **{y: v["entries"] for y,v in sk56["years"].items()}}
    with INDEX.open(encoding="utf-8-sig",newline="") as f:
        rows = [r for r in csv.DictReader(f) if int(r["tahun"]) in COUNTS]
    assert len(rows)==178
    results=[]
    for row in rows:
        y,n=row["tahun"],int(row["pdp"])
        sk,sp=row["sk"],row["sp"]
        candidate=candidates[y][sk]
        assert sp.rsplit(".",1)[0]==sk
        assert candidate.get("pdf_page",candidate.get("page"))==bank[y]["entries"][sp]["page"]
        assert candidate["academic_panel_signed_off"] is False
        dest=out/f"BA_T{y}_{n:03d}.docx"
        record=render(row,bank,dest,sk_candidate=candidate["text"],teacher=("4 Bestari","2027-01-20","08:00 - 09:00","30",""))
        doc=Document(dest)
        assert doc.tables[1].cell(0,1).text==sk+" "+candidate["text"]
        assert doc.tables[1].cell(1,1).text==sp+" "+bank[y]["entries"][sp]["text"]
        assert record["ready"] is False
        results.append(record)
    assert len({(r["year"],r["pdp"]) for r in results})==178
    assert all(sum(r["year"]==y for r in results)==n for y,n in COUNTS.items())
    (out/"report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("178 offline Word documents with candidate full SK/SP; no academic approval.")
if __name__=="__main__":
    main()
