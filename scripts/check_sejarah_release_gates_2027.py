#!/usr/bin/env python3
"""Contract QA: Sejarah 2027 must remain blocked while evidence incomplete."""
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from web.sejarah_2027_staging_source import SejarahNotReady, lesson, preview_only, source_fingerprint, source_paths

count=0
for y in (4,5,6):
    hashes=set()
    for n in range(1,37):
        row=preview_only(y,n)
        assert row["id"]==f"SEJ-T{y}-PDP-{n:03d}"
        identity=source_fingerprint(y,n)
        assert re.fullmatch(r"[0-9a-f]{64}",identity)
        hashes.add(identity)
        try:
            lesson(y,n)
        except SejarahNotReady:
            pass
        else:
            raise AssertionError(f"Unsafe Sejarah public release for Year {y} PdP {n}")
        count+=1
    assert len(hashes)==36
for args in [(3,1),(7,1),(4,0),(4,37),(4,True),(True,1)]:
    try:
        preview_only(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("Accepted invalid identifier "+str(args))
# Tampering with the lesson's own approval flags must NOT bypass the independent ledger.
import tempfile, shutil, json
with tempfile.TemporaryDirectory(prefix="sejarah-release-gate-") as temp:
    temp_root=Path(temp)
    y,n=6,1
    for relative in source_paths(y,n):
        src=ROOT/relative
        dest=temp_root/relative
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dest)
    ledger_rel=Path("audits/sejarah_y4_y6_release_approval_manifest_20261106.json")
    (temp_root/ledger_rel).parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/ledger_rel,temp_root/ledger_rel)
    json_rel=Path("rph_standalone/sejarah/y6_2027_rph_DRAF.json")
    obj=json.loads((temp_root/json_rel).read_text(encoding="utf-8"))
    x=obj["lessons"][0]["rph"]
    x["teacher_approval"]=True
    x["textbook_page_verified"]=True
    x["textbook_reference"]["exact_activity_page_confirmed"]=True
    x["status"]="FINAL_READY"
    x["release_signoff"]={
        "approved_by":"FORGED",
        "web_telegram_parity_verified":True,
        "word_pdf_layout_verified":True,
        "approved_source_fingerprint":"FORGED",
    }
    (temp_root/json_rel).write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")
    try:
        lesson(6,1,root=temp_root)
    except SejarahNotReady:
        pass
    else:
        raise AssertionError("Forged READY flags bypassed independent release ledger")

print(f"Sejarah fail-closed source contract: {count} / 108 previewable; all 108 public exports BLOCKED; 108 immutable fingerprints")
