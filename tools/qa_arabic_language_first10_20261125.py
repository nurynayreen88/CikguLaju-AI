"""Offline 55 full Arabic translations, no production mutation."""
import csv
import json
import re
from pathlib import Path
from docx import Document
from tools.arabic_178_draft_shared_layout_20261124 import ROOT, BANK, INDEX, render

def main():
    out = Path("qa-arabic-full-standards")
    out.mkdir(exist_ok=True)
    sk4 = json.loads((ROOT/"audits/arabic_draft_y4_sk_visual_candidates_20261125.json").read_text(encoding="utf-8"))
    sk56 = json.loads((ROOT/"audits/arabic_draft_y5_y6_sk_text_candidates_20261125.json").read_text(encoding="utf-8"))
    bank = json.loads(BANK.read_text(encoding="utf-8"))["years"]
    candidates = {"4": sk4["entries"], **{y: v["entries"] for y,v in sk56["years"].items()}}
    translations = json.loads((ROOT/"audits/arabic_language_first10_20261125.json").read_text(encoding="utf-8"))["records"]
    with INDEX.open(encoding="utf-8-sig",newline="") as f:
        rows = {(int(r["tahun"]), int(r["pdp"])):r for r in csv.DictReader(f)}
    assert len(translations)==55
    assert len({(t['year'], t['pdp']) for t in translations})==55
    for tr in translations:
        y,n=tr["year"],tr["pdp"]
        row=rows[y,n]
        t=tr["translation"]
        sk=candidates[str(y)][row["sk"]]["text"]
        dest=out/f"BA_T{y}_{n:03d}.docx"
        record=render(row,bank,dest,sk_candidate=sk,arabic_translation=tr)
        doc=Document(dest)
        visible="\n".join(c.text for table in doc.tables for r in table.rows for c in r.cells)
        assert not re.search(r"[A-Za-z]",visible), (y,n,visible)
        assert all(v in visible for v in t.values()), (y,n)
        assert doc.tables[1].cell(0,1).text==row["sk"]+" "+sk
        assert doc.tables[1].cell(1,1).text==row["sp"]+" "+bank[str(y)]["entries"][row["sp"]]["text"]
        assert record["ready"] is False
    tr=translations[0]
    row=rows[tr["year"],tr["pdp"]]
    manual=out/"manual-test.docx"
    render(row,bank,manual,arabic_translation=tr,manual_reflection="Catatan guru kekal.")
    assert Document(manual).tables[-1].cell(2,1).text=="Catatan guru kekal."
    manual.unlink()
    print("55/55 Arabic-only candidate documents; original teacher manual reflection unchanged.")
if __name__=="__main__":
    main()
