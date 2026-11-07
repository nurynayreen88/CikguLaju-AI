"""Produce a complete OFFLINE, printable review bundle of 342 Science RPHs.

No server, login, runtime AI, textbook binary, DB mutation or user credits.
This is a professional self-contained *internal review* tool, NOT public
publication of lessons with unverified curriculum/book/panitia evidence.
Requires all 342 actually generated one-page-A4 PDFs and Word counterparts.
"""
from __future__ import annotations

import csv
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import shutil
import zipfile

from docx import Document
from pypdf import PdfReader

from tools.audit_rph80_sains_first_20261107 import EXPECTED
from tools.export_sains_342_panitia_review_20261107 import get_review_rows
from web.sains_rph_quality_release_gate_20261108 import approved_count

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/sains_342_offline_review_20261108"
PORTAL=OUT/"SAINS_342_OFFLINE_SEMAKAN_DRAF"
ZIP=OUT/"SAINS_342_RPH_WORD_PDF_SEMAKAN_DRAF.zip"
VALID_STATUS="HOLD — AKADEMIK BELUM DISAHKAN"


def _pdf_ok(path:Path,code:str):
    reader=PdfReader(str(path))
    if len(reader.pages)!=1:
        raise ValueError(f"{code}: PDF is not one page A4")
    box=reader.pages[0].mediabox
    if abs(float(box.width)-595.28)>2 or abs(float(box.height)-841.89)>2:
        raise ValueError(f"{code}: PDF dimensions not A4")
    text=reader.pages[0].extract_text()
    if not all(x in text for x in ("Aktiviti 1","Aktiviti 2")):
        raise ValueError(f"{code}: missing phases from PDF")
    return len(text)


def _row_html(row,filename_pdf,filename_word):
    code=row["Kod PdP"]
    title=row["Tajuk calon dalam RPH"] or row["Tajuk PdP"]
    alert="; ".join(x for x in (
        row["Amaran konflik sumber asal"],row["Isu SP berganda"],
        row["Buku Teks — status muka surat SP"]) if x)
    sksp=f'SK {row["SK"]} · SP {row["SP"]}'
    search=" ".join((str(row["Tahun"]),code,title,row["Unit"],sksp)).casefold()
    y=int(row["Tahun"])
    def safe(x):return escape(str(x),quote=True)
    return (
        f'<tr data-year="{y}" data-search="{safe(search)}">'
        f'<td><strong>{safe(code)}</strong><small>{safe(row["Unit"])}</small></td>'
        f'<td>{safe(title)}<small>{safe(sksp)}</small></td>'
        f'<td><span class="hold">BELUM DISAHKAN</span><small>{safe(alert)}</small></td>'
        f'<td class="downloads"><a href="{safe(filename_word)}" download>Word</a>'
        f'<a href="{safe(filename_pdf)}" download>PDF</a></td></tr>'
    )


def _html(rows):
    trs="\n".join(_row_html(row,row["_pdf"],row["_word"]) for row in rows)
    return """<!doctype html>
<html lang="ms"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sains • 342 RPH • Semakan dalaman CikguLaju</title>
<style>
:root{color-scheme:light;font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#172b3d;background:#f3f6f8}
*{box-sizing:border-box}body{margin:0}header{padding:32px max(20px,calc((100vw - 1160px)/2));background:#13384f;color:#fff}
h1{font-size:clamp(24px,3.5vw,38px);margin:0 0 12px}p{line-height:1.55}header p{max-width:860px;margin:0;opacity:.95}
main{max-width:1200px;margin:0 auto;padding:20px}.notice{background:white;border-left:5px solid #b66b32;padding:17px;margin-bottom:20px}
.controls{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0}.controls label{display:flex;flex-direction:column;gap:7px;font-weight:600}
input,select{border:1px solid #9aabba;border-radius:7px;background:white;padding:12px;font:inherit;min-width:185px}
input{min-width:min(400px,calc(100vw - 48px))}.count{align-self:end;padding:12px}
.table{overflow-x:auto;border:1px solid #d7dfe5;border-radius:8px;background:#fff}table{border-collapse:collapse;width:100%;min-width:800px}
th,td{padding:14px 13px;text-align:left;vertical-align:top;border-bottom:1px solid #e7ebee}th{background:#e4edf3;position:sticky;top:0}
td small{display:block;color:#5d7180;margin-top:6px;line-height:1.5}td:first-child{min-width:190px}.hold{color:#9d5612;font-weight:700;font-size:12px}
.downloads{white-space:nowrap}.downloads a{display:inline-block;color:#095b87;padding:8px;border:1px solid #9ec4dd;border-radius:6px;margin-right:4px;text-decoration:none;font-weight:600}
.downloads a:focus,.downloads a:hover{background:#eef7fc}
.note{font-size:13px;color:#5d7180}footer{padding:28px 0;font-size:13px;color:#526676}
@media print{header{background:white;color:black}.controls{display:none}.downloads{display:none}body{background:#fff}.notice{border:1px solid #555}}
</style></head><body><header><h1>RPH Sains Tahun 2–6</h1>
<p>342 RPH dalam Word dan PDF yang boleh dibuka tanpa internet. Pilih tahun, cari unit atau PdP dan buka fail. Pakej semakan ini bukan penerbitan RPH yang diluluskan untuk guru.</p></header>
<main><section class="notice"><strong>STATUS: DRAF / UNTUK SEMAKAN DALAMAN SAHAJA</strong>
<p>Semua 342 RPH belum menerima kelulusan akademik individu. Semak SK/SP, halaman Buku Teks/Buku Aktiviti, aktiviti khusus, keselamatan, PBD individu dan RPT sebelum menggunakannya dalam kelas. Konflik sumber disenaraikan pada setiap baris. Jangan edar sebagai bahan FINAL READY.</p>
<p><a href="SEMAKAN_PANITIA_342.csv" download>Senarai semakan guru/panitia (CSV)</a> · <a href="PANDUAN_SEMAKAN.txt" download>Panduan (TXT)</a></p></section>
<div class="controls"><label for="year">Tahun<select id="year"><option value="">Semua tahun (342)</option>
<option value="2">Tahun 2 (51)</option><option value="3">Tahun 3 (45)</option>
<option value="4">Tahun 4 (79)</option><option value="5">Tahun 5 (83)</option>
<option value="6">Tahun 6 (84)</option></select></label>
<label for="q">Cari PdP, SP atau tajuk<input id="q" type="search" placeholder="Contoh: 3.1.3, jirim, Unit 5"></label>
<span id="count" aria-live="polite" class="count">342 daripada 342 RPH</span></div>
<div class="table"><table><thead><tr><th>PdP / Unit</th><th>Tajuk / SK-SP</th>
<th>Status / perkara perlu semak</th><th>Fail</th></tr></thead><tbody>
""" + trs + """</tbody></table></div>
<footer>Disediakan daripada sumber RPH CikguLaju dan audit DSKP; bukan dokumen Buku Teks KPM. Tiada akaun, kuota, pembayaran atau database disentuh.</footer>
</main><script>
(()=>{const y=document.getElementById('year'),q=document.getElementById('q'),counter=document.getElementById('count');
const rows=[...document.querySelectorAll('tbody tr')];function filter(){
const v=y.value,t=q.value.trim().toLocaleLowerCase('ms-MY');let shown=0;
for(const row of rows){const ok=(!v||row.dataset.year===v)&&(!t||row.dataset.search.includes(t));
row.hidden=!ok;if(ok)shown++;}
counter.textContent=shown+' daripada 342 RPH';}
y.addEventListener('change',filter);q.addEventListener('input',filter);filter();})();
</script></body></html>
"""


def build():
    rows=get_review_rows()
    if len(rows)!=342 or approved_count()!=0:
        raise RuntimeError("Not the original 342 pending-academic-approval roster")
    if OUT.exists():
        shutil.rmtree(OUT)
    PORTAL.mkdir(parents=True)
    output=[];manifest=[];numbers={year:set() for year in EXPECTED}
    for record in rows:
        row=dict(record);year=int(row["Tahun"])
        code=row["Kod PdP"]
        no=int(code.rsplit("-",1)[1])
        if year not in EXPECTED or no in numbers[year]:
            raise ValueError("Unexpected/duplicated Year2-6 PdP identity "+code)
        numbers[year].add(no)
        if row["Keputusan"]!=VALID_STATUS or row["Aktif di Telegram/Web"] is not False:
            raise ValueError("Year2-6 source is marked public without approval "+code)
        if row["QA cetakan Word/PDF"]!="SINGLE_A4_TECHNICAL_PASS":
            raise ValueError("RPH source document A4 not yet mechanically verified "+code)
        files={}
        for kind,field,ext in [
            ("word","Word RPH staging",".docx"),
            ("pdf","PDF RPH staging",".pdf")]:
            path=ROOT/row[field]
            expected=f"SAINS_T{year}_PDP_{no:03d}_DRAF{ext}"
            if path.name!=expected or not path.is_file() or path.is_symlink():
                raise FileNotFoundError("Incorrect/missing authored RPH "+code+": "+str(path))
            if kind=="pdf":
                _pdf_ok(path,code)
            else:
                doc=Document(str(path))
                if not doc.tables or not doc.sections:
                    raise ValueError("Word document missing structural tables "+code)
                sec=doc.sections[0]
                if (abs(sec.page_width.cm-21)>0.05 or
                    abs(sec.page_height.cm-29.7)>0.05):
                    raise ValueError("Word not A4 "+code)
            relative=Path(f"Tahun_{year}")/kind/path.name
            dest=PORTAL/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,dest)
            files[kind]=str(relative).replace("\\","/")
        row["_pdf"]=files["pdf"];row["_word"]=files["word"]
        output.append(row)
        manifest.append({
            "pdp_code":code,"year":year,"sk":row["SK"],"sp":row["SP"],
            "draft":True,"teacher_approved":False,
            "word":files["word"],"pdf":files["pdf"],
            "word_sha256":sha256((PORTAL/files["word"]).read_bytes()).hexdigest(),
            "pdf_sha256":sha256((PORTAL/files["pdf"]).read_bytes()).hexdigest(),
        })
    for year,total in EXPECTED.items():
        if numbers[year]!=set(range(1,total+1)):
            raise ValueError("Year2-6 source contains gaps "+str(year))
    (PORTAL/"index.html").write_text(_html(output),encoding="utf-8")
    with (PORTAL/"SEMAKAN_PANITIA_342.csv").open("w",encoding="utf-8-sig",newline="") as f:
        public_columns=[x for x in rows[0] if not x.startswith("_")]
        writer=csv.DictWriter(f,fieldnames=public_columns)
        writer.writeheader()
        writer.writerows({key:r[key] for key in public_columns} for r in output)
    (PORTAL/"PANDUAN_SEMAKAN.txt").write_text(
        "SAINS 342 RPH — DRAF SEMAKAN, BUKAN READY UNTUK PENGGUNA\n"
        "1. Ekstrak keseluruhan ZIP ke satu folder.\n"
        "2. Buka index.html dalam pelayar. Gunakan carian Tahun / PdP / SP.\n"
        "3. Klik Word atau PDF; pautan berfungsi tanpa internet.\n"
        "4. Rekod semakan guru/panitia dalam SEMAKAN_PANITIA_342.csv.\n"
        "5. SP Tahun 2 3.1.4–3.1.6 masih perlu pemetaan RPT; Tahun 4 dan 6 "
        "perlu semakan halaman BT sebenar; T3 tiga PdP berbilang SP "
        "perlu pengesahan PBD kedua.\n"
        "6. Jangan muat naik ke Web/Telegram atau tandakan FINAL READY "
        "sebelum kelulusan akademik individu.\n"
        "Tiada Buku Teks asal disertakan dalam pakej.\n",encoding="utf-8")
    (PORTAL/"MANIFEST_SHA256.json").write_text(
        json.dumps({"status":"ACADEMIC_HOLD","approved":0,
                    "counts":{str(k):v for k,v in EXPECTED.items()},
                    "items":manifest},indent=2,ensure_ascii=False)+"\n",
        encoding="utf-8")
    with zipfile.ZipFile(ZIP,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for file in sorted(PORTAL.rglob("*")):
            if file.is_file():
                z.write(file,str(Path(PORTAL.name)/file.relative_to(PORTAL)))
    with zipfile.ZipFile(ZIP) as z:
        member_names=z.namelist()
        if len(member_names)!=2*342+4 or any(name.startswith("/") or ".." in Path(name).parts
            for name in member_names):
            raise ValueError("Incomplete/unsafe packaged review bundle")
        if not all(z.getinfo(Path(PORTAL.name,rec[k]).as_posix()).file_size>500
            for rec in manifest for k in ("word","pdf")):
            raise ValueError("Corrupted or missing authored Word/PDF in ZIP")
    print(f"SAINS_OFFLINE_REVIEW: {len(output)} Word + {len(output)} PDF; "
          f"all 342 selected by Tahun/PdP; {ZIP.stat().st_size} bytes; "
          "NO FINAL READY, 0 approved, NO LIVE RUNTIME")


if __name__=="__main__":
    build()
