#!/usr/bin/env python3
"""Verify Sejarah content hashes are achievable and isolated per PdP.

No real approvals are modified, no permanent RPH file is written. A temporary
mirror proves an unrelated PdP cannot invalidate another approved digest.
"""
import csv
from io import StringIO
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from web.sejarah_2027_source_hash import fingerprint,source_paths
from web.rph_shared_source_identity import source_fingerprint as shared

for y in (4,5,6):
    for n in range(1,37):
        digest=fingerprint(y,n)
        assert isinstance(digest,str) and len(digest)==64,(y,n)
        assert digest==shared(y,"SEJARAH",n),(y,n)

with tempfile.TemporaryDirectory(prefix="sejarah-hash-scope-") as temp:
    root=Path(temp)
    for n in (1,2):
        for rel in source_paths(4,n):
            src=ROOT/rel
            dst=root/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            if not dst.exists(): shutil.copy2(src,dst)
    p=root/"rph_standalone/sejarah/y4_2027_rph_DRAF.json"
    baseline1=fingerprint(4,1,root=root)
    baseline2=fingerprint(4,2,root=root)
    assert baseline1!=baseline2

    obj=json.loads(p.read_text(encoding="utf-8"))
    obj["lessons"][1]["rph"]["bbm"]+=" TEST_OTHER_LESSON"
    p.write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
    assert fingerprint(4,1,root=root)==baseline1,"Other lesson changed fingerprint"
    assert fingerprint(4,2,root=root)!=baseline2,"Own lesson did not change"

    obj["lessons"][1]["rph"]["bbm"]=obj["lessons"][1]["rph"]["bbm"].replace(" TEST_OTHER_LESSON","")
    p.write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
    assert fingerprint(4,2,root=root)==baseline2,"Original hash did not restore"

    approval=obj["lessons"][0]["rph"].setdefault("release_signoff",{})
    approval["approved_source_fingerprint"]="A"*64
    p.write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
    assert fingerprint(4,1,root=root)==baseline1,"Self-referential approval digest"
    approval["approved_source_fingerprint"]=baseline1
    p.write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
    assert fingerprint(4,1,root=root)==baseline1,"Cannot store matching approved hash"

    approval["approved_by"]="TEST_REVIEWER_NOT_ACTUAL_APPROVAL"
    p.write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
    assert fingerprint(4,1,root=root)!=baseline1,"Approval signer tamper not detected"
    del obj["lessons"][0]["rph"]["release_signoff"]
    p.write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
    assert fingerprint(4,1,root=root)==baseline1

    csvfile=root/"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_4_2027_A_B_DRAF.csv"
    with csvfile.open(encoding="utf-8",newline="") as fin:
        reader=csv.DictReader(fin)
        header=reader.fieldnames
        rows=list(reader)
    rows[1]["Evidens PBD RPH"]+=" _OTHER_PDP_QA"
    with csvfile.open("w",encoding="utf-8",newline="") as fout:
        writer=csv.DictWriter(fout,fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    assert fingerprint(4,1,root=root)==baseline1,"Unrelated RPT row changed digest"
    assert fingerprint(4,2,root=root)!=baseline2,"Own RPT row not included"
    rows[0]["Evidens PBD RPH"]+=" _SELF_PDP_QA"
    with csvfile.open("w",encoding="utf-8",newline="") as fout:
        writer=csv.DictWriter(fout,fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    assert fingerprint(4,1,root=root)!=baseline1,"Own RPT row not protected"

    md=root/"rph_standalone/sejarah/tahun_4/RPH_SEJ-T4-PDP-001.md"
    md.write_text(md.read_text(encoding="utf-8")+"\nQA MD MODIFICATION\n",encoding="utf-8")
    assert fingerprint(4,1,root=root)!=baseline1,"Markdown changes not protected"

print("Sejarah 108 individual fingerprints PASS; independence, self-signoff, RPT and Markdown tamper checks PASS")
