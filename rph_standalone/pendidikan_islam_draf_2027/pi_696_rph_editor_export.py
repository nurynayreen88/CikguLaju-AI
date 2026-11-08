"""Export a complete 696-PdP Pendidikan Islam *review* collection.

Produces editable DOCX and PDF per PdP plus year-level PDF binders and
review indexes. Every output is plainly marked "DRAF STAGING" and may only
be accessed via GitHub Actions' restricted audit artifacts. This is NOT
teacher publication or a replacement for the native CikguLaju generator.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED

from pi_editor_jawi_closing_projection import preview as jawi_preview
from pi_held_six_editor_candidate_packet import audit as held_packet
from pi_held_six_word_pdf_print_audit import normalize as normalize_held
from pi_quality_audit import COUNT
from pi_surah_pbd_alignment_audit import RPT_SOURCE_ERRORS
from pi_y5_activity_book_wording_review import EXPECTED as YEAR5_ACTIVITY_BOOK_AMBIGUOUS
from pi_word_pdf_print_audit import make_docx, inspect_pdf

CRITICAL = {"T4-L083", "T6-L137", "T6-L141"}
HELD = {"T2-L035", "T6-L006", "T6-L014", "T6-L018", "T6-L060", "T6-L117"}
JUZ25_UNMAPPED_SOURCE = {
    "T6-L002", "T6-L006", "T6-L010", "T6-L014", "T6-L018",
    "T6-L022", "T6-L026"
}

def academic_warning_codes(entry, page_count):
    """Make source problems visible to the editor even for one-page A4 PDFs.

    Codes reflect existing review audits; they certify neither academic content
    nor the production Word/PDF generator. Original source stays immutable.
    """
    ident = entry["record"]["id"]
    codes = ["ACADEMIC_AND_JAWI_APPROVAL_PENDING"]
    if ident in HELD:
        codes.append("SOURCE_RECORD_WITHHELD_EDITOR_CANDIDATE_ONLY")
    if ident in CRITICAL:
        codes.append("CRITICAL_HADITH_OR_TASMI_SOURCE_HOLD")
    if ident in RPT_SOURCE_ERRORS:
        codes.append("ORIGINAL_RPT_SURAH_LABEL_ERROR_PENDING")
    if ident == "T4-L107":
        codes.append("ORIGINAL_RPT_YEAR4_PUASA_SIX_RUKUN_ERROR_PENDING")
    if ident == "T3-L059":
        codes.append("ORIGINAL_RPT_YEAR3_SOLAT_OBJECTIVE_SEQUENCE_ERROR_PENDING")
    if ident in YEAR5_ACTIVITY_BOOK_AMBIGUOUS:
        codes.append("YEAR5_BUKU_AKTIVITI_EDITION_AND_EXERCISE_UNVERIFIED")
    if ident in JUZ25_UNMAPPED_SOURCE:
        codes.append("ORIGINAL_RPT_YEAR6_JUZ25_67_AYAT_UNMAPPED")
    if ident == "T2-L035":
        codes.append("ORIGINAL_RPT_YEAR2_AYAH224_OVERLAP_UNRESOLVED")
    if entry["source_bahan_notes"]:
        codes.append("EDITOR_ONLY_SOURCE_MATERIAL_NOTES_HELD_SEPARATELY")
    if page_count != 1:
        codes.append("PDF_LAYOUT_NOT_ONE_PAGE")
    return codes
COLUMNS = (
    "id", "year", "lesson", "review_status", "ready_for_teacher",
    "source_sp_approved", "jawi_approved", "file_docx", "file_pdf",
    "pdf_pages", "one_page_a4", "warning"
)
DISCLAIMER = """CIKGULAJU PENDIDIKAN ISLAM — 2027 / TAHUN 2–6

HANYA UNTUK SEMAKAN EDITOR PROJEK. BUKAN RPH FINAL READY.
Jangan sebarkan kepada guru melalui Telegram/Web.

Katalog: 696 PdP = 690 draf rekod sumber + 6 calon terasing.
Tiga RPH (T4-L083, T6-L137, T6-L141) sumber kritikal.
Enam RPH asal (T2-L035; T6-L006,014,018,060,117) kekal withheld;
versi dalam ZIP ialah calon editorial, BUKAN rekod rasmi.
Penutup 690 RPH ditukarkan kepada cadangan Jawi untuk semakan sahaja.
78 kumpulan calon Jawi belum mendapat kelulusan ejaan/pakar.
Juzuk 25 Tahun 6: 67 ayat masih belum dipetakan dalam RPT asal.
T2 PdP035: pertindihan al-Baqarah 224 dengan PdP032 belum diputuskan.
Buku Aktiviti Tahun 2/3: 174 latihan muka surat/SP belum disahkan.
Reka letak A4 bukan bukti ketepatan SK/SP, tajwid, fiqh atau Jawi.

Fail Word/PDF bagi setiap PdP ialah DRAF bertanda untuk reviewer.
RPT asal, DB, bot, login, langganan dan produksi tidak diubah.
"""

def gather(root=None):
    # Root is optional for normal CI, testing can supply a fixture path.
    kw={} if root is None else {"root":root}
    nonheld=jawi_preview(**kw)
    held=held_packet(**kw)
    assert nonheld["jawi_closing_candidates_injected_in_reversible_preview"] == 690
    assert held["fully_held_editor_candidates"]==6
    rows={}
    for item in nonheld["rows"]:
        ident=item["id"]
        year=int(ident.split("-")[0][1:])
        lesson=int(ident.split("-")[1][1:])
        assert ident not in HELD and ident not in rows
        status=("CRITICAL_SOURCE_HOLD" if ident in CRITICAL
                else "UNVERIFIED_RPH_DRAFT")
        rows[ident]={
            "record":{"id":ident,"tahun":year,"lesson":lesson,
                      "fields":item["display_fields"]},
            "review_status":status,
            "original_rumi_penutup":item["original_penutup_rumi"],
            "source_bahan_notes":item["editor_only_material_notes"],
        }
    for item in held["rows"]:
        ident=item["id"]
        assert ident in HELD and ident not in rows
        rows[ident]={
            "record":normalize_held(item),
            "review_status":"ORIGINAL_HELD_EDITOR_CANDIDATE",
            "original_rumi_penutup":None,
            "source_bahan_notes":[],
        }
    assert len(rows)==696
    summary=Counter(int(k.split("-")[0][1:]) for k in rows)
    assert dict(summary)==COUNT,summary
    assert sum(v["review_status"]=="CRITICAL_SOURCE_HOLD" for v in rows.values())==3
    assert sum(v["review_status"]=="ORIGINAL_HELD_EDITOR_CANDIDATE" for v in rows.values())==6
    return [rows[k] for k in sorted(rows, key=lambda x:(int(x.split("-")[0][1:]),
                                                        int(x.split("-")[1][1:])))]

def create_report(output_dir, *, sample=0, batch_size=24):
    # LibreOffice requires an absolute file:// UserInstallation URI. A relative
    # URI is parsed as a hostname and can hang until subprocess timeout.
    output_dir=Path(output_dir).resolve();output_dir.mkdir(parents=True,exist_ok=True)
    exe=shutil.which("libreoffice") or shutil.which("soffice")
    if not exe:
        raise RuntimeError("LibreOffice is required for real Word/PDF export")
    from pypdf import PdfReader, PdfWriter

    source=gather()
    if sample:
        # Always include all six held, all three critical and beginning/end
        # of every year, then deterministic extra lessons.
        selected={entry["record"]["id"] for entry in source
                  if entry["review_status"]!="UNVERIFIED_RPH_DRAFT"}
        for year in COUNT:
            rows=[x for x in source if x["record"]["tahun"]==year]
            selected.update([rows[0]["record"]["id"],rows[-1]["record"]["id"]])
        for entry in source:
            if len(selected)>=sample:
                break
            selected.add(entry["record"]["id"])
        source=[x for x in source if x["record"]["id"] in selected]
    work=[]
    readme=output_dir/"README_SEMAKAN_EDITOR.txt"
    readme.write_text(DISCLAIMER,encoding="utf-8")
    for entry in source:
        r=entry["record"]
        year=r["tahun"]
        folder=output_dir/f"Tahun_{year}"
        word=folder/"Word"
        pdf=folder/"PDF"
        word.mkdir(parents=True,exist_ok=True)
        pdf.mkdir(parents=True,exist_ok=True)
        path=word/(r["id"]+".docx")
        make_docx(r,path)
        assert path.stat().st_size>1000,r["id"]
        work.append((entry,path,pdf/(r["id"]+".pdf")))

    # LibreOffice batch invocation reuses an isolated profile. Avoid publishing
    # generated draft documents in an environment accessed by end users.
    for start in range(0,len(work),batch_size):
        batch=work[start:start+batch_size]
        pdf_dir=batch[0][2].parent
        # Batch across years only if one output dir; group by year first.
        for pathdir in sorted({pdf.parent for _,_,pdf in batch}):
            subset=[path for _,path,pdf in batch if pdf.parent==pathdir]
            cmd=[exe,"-env:UserInstallation=file://"+str(output_dir/".lo_profile"),
                 "--headless","--convert-to","pdf","--outdir",str(pathdir)]
            cmd.extend(str(path) for path in subset)
            run=subprocess.run(cmd,capture_output=True,text=True,timeout=360)
            if run.returncode!=0:
                raise RuntimeError(f"LibreOffice failed for {pathdir}: {run.stderr[-700:]}")
    records=[]
    for entry,word,pdf in work:
        r=entry["record"]
        if not pdf.is_file():
            raise RuntimeError("PDF conversion missing: "+r["id"])
        pages,a4,chars=inspect_pdf(pdf)
        assert pages>=1 and a4 and pdf.stat().st_size>1000,(r["id"],pages,a4)
        if chars==0:
            raise RuntimeError("PDF text extraction empty: "+r["id"])
        warning_codes = academic_warning_codes(entry, pages)
        records.append({
            "id":r["id"],"year":r["tahun"],"lesson":r["lesson"],
            "review_status":entry["review_status"],
            "ready_for_teacher":False,
            "source_sp_approved":False,"jawi_approved":False,
            "file_docx":f"Tahun_{r['tahun']}/Word/{word.name}",
            "file_pdf":f"Tahun_{r['tahun']}/PDF/{pdf.name}",
            "pdf_pages":pages,
            "one_page_a4":pages==1,
            "warning":" | ".join(warning_codes)
        })
    assert len(records)==len(source)
    warning_counts=Counter(
        code for item in records for code in item["warning"].split(" | ")
    )
    assert warning_counts["ACADEMIC_AND_JAWI_APPROVAL_PENDING"] == len(records)
    if not sample:
        assert warning_counts["SOURCE_RECORD_WITHHELD_EDITOR_CANDIDATE_ONLY"] == 6
        assert warning_counts["CRITICAL_HADITH_OR_TASMI_SOURCE_HOLD"] == 3
        assert warning_counts["ORIGINAL_RPT_SURAH_LABEL_ERROR_PENDING"] == 7
        assert warning_counts["ORIGINAL_RPT_YEAR4_PUASA_SIX_RUKUN_ERROR_PENDING"] == 1
        assert warning_counts["ORIGINAL_RPT_YEAR3_SOLAT_OBJECTIVE_SEQUENCE_ERROR_PENDING"] == 1
        assert warning_counts["YEAR5_BUKU_AKTIVITI_EDITION_AND_EXERCISE_UNVERIFIED"] == 13
        assert warning_counts["ORIGINAL_RPT_YEAR6_JUZ25_67_AYAT_UNMAPPED"] == 7
        assert warning_counts["ORIGINAL_RPT_YEAR2_AYAH224_OVERLAP_UNRESOLVED"] == 1
    (output_dir/"INDEX_EDITOR_696.json").write_text(
        json.dumps({"status":"DRAF_EDITOR_ONLY_NO_GO",
                    "catalog_total":696,
                    "files_rendered":len(records),
                    "one_page_a4":sum(r["one_page_a4"] for r in records),
                    "not_one_page_ids":[r["id"] for r in records if not r["one_page_a4"]],
                    "all_source_documents_untouched":True,
                    "warning_code_counts":dict(sorted(warning_counts.items())),
                    "year1_kp2027_out_of_scope":True,
                    "ready_for_teacher":0,
                    "rows":records},ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8")
    with (output_dir/"INDEX_EDITOR_696.csv").open("w",newline="",encoding="utf-8-sig") as s:
        writer=csv.DictWriter(s,fieldnames=COLUMNS)
        writer.writeheader();writer.writerows(records)
    year_binders={}
    for year in COUNT:
        yr_rows=[r for r in records if r["year"]==year]
        if not yr_rows:
            continue
        pdf_root=output_dir/f"Tahun_{year}"/"PDF"
        writer=PdfWriter()
        for entry in yr_rows:
            src=PdfReader(str(pdf_root/(entry["id"]+".pdf")))
            for page in src.pages:
                writer.add_page(page)
        binder=output_dir/f"Tahun_{year}"/f"RPH_Pendidikan_Islam_Tahun_{year}_DRAF_SEMAKAN.pdf"
        with binder.open("wb") as f:
            writer.write(f)
        assert binder.stat().st_size>5000
        year_binders[str(year)]=str(binder.relative_to(output_dir))
    zipped=[]
    for year in COUNT:
        ydir=output_dir/f"Tahun_{year}"
        if not ydir.exists():
            continue
        archive=output_dir/f"RPH_PI_Tahun_{year}_DRAF_SEMAKAN_Word_PDF.zip"
        with ZipFile(archive,"w",compression=ZIP_DEFLATED,compresslevel=6) as z:
            z.write(readme,"README_SEMAKAN_EDITOR.txt")
            for p in sorted(ydir.rglob("*")):
                if p.is_file():
                    z.write(p,p.relative_to(output_dir))
        assert archive.stat().st_size>2000
        zipped.append(str(archive.relative_to(output_dir)))
    metadata={
        "status":"DRAF_EDITOR_ONLY_NO_GO",
        "expected_catalog_total":696,
        "rendered_docx":len(records),
        "rendered_pdf":len(records),
        "one_page_a4":sum(x["one_page_a4"] for x in records),
        "warning_code_counts":dict(sorted(warning_counts.items())),
        "a4_binder_by_year":year_binders,
        "year_archives":zipped,
        "source_data_modified":False,
        "teacher_publishable":0,
        "jawi_approved":0,
        "expert_approved":0,
        "native_web_telegram_verified":False,
        "academic_quality_percent":None
    }
    (output_dir/"RUN_SUMMARY.json").write_text(
        json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(metadata,ensure_ascii=False,indent=2),flush=True)
    if not sample and len(records)!=696:
        raise ValueError("Expected exactly 696 full review RPH outputs")
    return metadata

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    ap.add_argument("--sample",type=int,default=0)
    ap.add_argument("--batch-size",type=int,default=24)
    args=ap.parse_args()
    create_report(args.output,sample=args.sample,batch_size=args.batch_size)
