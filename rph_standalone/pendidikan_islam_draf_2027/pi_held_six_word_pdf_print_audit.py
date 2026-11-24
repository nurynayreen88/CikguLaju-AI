"""Print six quarantined editor-only RPH proposals to temporary Word/PDF A4.

The main catalog still contains no teaching fields for held records. This
test does not approve Quran interpretation, DSKP, Jawi, native Web/Telegram
rendering, or distribute any PDF. Only QA metadata is retained.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from pi_held_six_editor_candidate_packet import audit as packet
from pi_word_pdf_print_audit import A4, inspect_pdf, make_docx


def normalize(lesson):
    ident=lesson["id"]
    year=int(ident.split("-")[0][1:])
    num=int(ident.split("-")[1][1:])
    src=lesson["candidate"]
    objective=src.get("learning_outcomes") or src.get("objective")
    assert isinstance(objective,list) and len(objective)>=2
    sk=src.get("sk_provenance") or src.get("sk")
    sp=src.get("sp_source_text") or (
        "Kod SP untuk aktiviti amali tambahan: " + ", ".join(src["sp_codes"])
        if src.get("sp_codes") else
        "Julat bacaan berpandukan RPT; jangan nyatakan kod SP rasmi yang tiada"
    )
    activity=src["aktiviti_utama"]
    assert len(activity)==4 and all(s.startswith(f"{n}. ") for n,s in enumerate(activity,1))
    fields={
      "sk":sk,"sp":sp,
      "objektif":"\n".join(f"{i}. {value}" for i,value in enumerate(objective,1)),
      "set_induksi":src["set_induksi"],
      "aktiviti_utama":"\n".join(activity),
      "pentaksiran":src["pentaksiran"],
      "penutup":src["penutup"],
      "bahan":src["bahan"]
    }
    assert all(isinstance(value,str) and value.strip() for value in fields.values())
    return {"id":ident,"tahun":year,"lesson":num,"fields":fields}


def audit(*,output):
    if not (shutil.which("libreoffice") or shutil.which("soffice")):
        raise RuntimeError("LibreOffice not present")
    rows=packet()["rows"]
    assert len(rows)==6
    results=[]
    with tempfile.TemporaryDirectory(prefix="pi_six_rph_editor_") as folder:
        folder=Path(folder)
        wd,pd=folder/"word",folder/"pdf"
        wd.mkdir();pd.mkdir()
        for row in rows:
            r=normalize(row)
            path=wd/(r["id"]+".docx")
            make_docx(r,path)
        exe=shutil.which("libreoffice") or shutil.which("soffice")
        cmd=[exe,"-env:UserInstallation=file://"+str(folder/"profile"),
             "--headless","--convert-to","pdf","--outdir",str(pd)]
        cmd.extend(str(p) for p in sorted(wd.glob("*.docx")))
        run=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        assert run.returncode==0,(run.stderr[-700:],run.stdout[-400:])
        for row in rows:
            ident=row["id"]
            wf=wd/(ident+".docx")
            pf=pd/(ident+".pdf")
            assert pf.is_file(),ident
            pages,a4,chars=inspect_pdf(pf)
            results.append({
                "id":ident,
                "source_still_held":True,
                "diagnostic_only":True,
                "word_bytes":wf.stat().st_size,
                "pdf_bytes":pf.stat().st_size,
                "pdf_pages":pages,
                "all_pages_a4":a4,
                "one_page_a4":pages==1 and a4,
                "pdf_extracted_characters":chars,
                "jawi_visual_approval":False,
                "source_sp_expert_approval":False,
                "word_pdf_native_bot_tested":False,
                "can_publish":False,
                "release":"NO_GO"
            })
    assert len(results)==6 and len({r["id"] for r in results})==6
    result={
        "scope":"TEMPORARY_RUMI_EDITOR_CANDIDATE_6_NOT_PRODUCTION",
        "editor_candidates_printed":6,
        "one_page_a4_count":sum(r["one_page_a4"] for r in results),
        "all_converted":all(r["pdf_bytes"]>0 for r in results),
        "expert_approved":0,
        "runtime_verified":0,
        "original_held_catalog_entries_modified":False,
        "document_binaries_not_distributed":True,
        "publication":"HOLD","release":"NO_GO",
        "rows":results
    }
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
    if result["one_page_a4_count"]!=6:
        raise ValueError("Six editor proposals must fit one A4; inspect QA report before release")
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    audit(output=args.output)
