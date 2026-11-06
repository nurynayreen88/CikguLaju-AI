#!/usr/bin/env python3
"""Render RBT 2027 staging *HTML previews*, never production downloads.

Output is draft visual HTML only. This script does not create Word/PDF files,
mark anything approved, schedule classes, or write to the curriculum DB.
"""
from __future__ import annotations
import argparse
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def h(value):
    return html.escape(str(value if value is not None else ""), quote=True)

def css(portrait=True):
    orientation = "portrait" if portrait else "landscape"
    return f"""
@page {{size: A4 {orientation}; margin: 10mm 12mm;}}
* {{ box-sizing: border-box; }}
html, body {{margin:0; padding:0; color:#253343; background:#fff; font-family:Arial, sans-serif;}}
h1,h2,p {{margin:0 0 5px;}}
h1 {{font-size:21px; color:#183e6d; letter-spacing:.3px;}}
h2 {{font-size:13px; color:#183e6d;}}
small,.muted {{font-size:9px; color:#586778;}}
.status {{display:inline-block; border:1px solid #7d92a8; color:#34475d; padding:3px 7px; font-size:9px; border-radius:7px;}}
.header {{border-bottom:2px solid #224f78; margin-bottom:9px; padding-bottom:7px;}}
table {{border-collapse:collapse; width:100%; margin-top:6px; font-size:10px; line-height:1.3;}}
th,td {{border:1px solid #9eb0c2; padding:5px 6px; vertical-align:top;}}
th {{background:#eaf0f5; color:#1a3656; text-align:left;}}
.rule {{border-top:1px solid #ccd6e0; margin:8px 0;}}
.notes {{font-size:9px; color:#3d5166; background:#f3f6f8; padding:7px 8px; margin-top:8px;}}
.layout {{display:grid; grid-template-columns:1fr 1fr; gap:6px;}}
.page {{page-break-after:always; break-after:page; page-break-inside:avoid; break-inside:avoid-page;}}
.page:last-child {{page-break-after:auto; break-after:auto;}}
.cover {{min-height:165mm; display:flex; flex-direction:column; justify-content:center; padding:20mm; background:#f2f6fa; border-left:12px solid #1e4f75;}}
.cover .title {{font-size:32px; font-weight:bold; color:#173d60; margin:0 0 12px;}}
.rph {{font-size:10px; line-height:1.25;}}
.rph table {{font-size:9.5px; line-height:1.25;}}
.rph th,.rph td {{padding:4px 5px;}}
.rph .main {{margin-bottom:5px;}}
@media screen {{body {{padding:18px; max-width:1100px; margin:auto; background:#f6f8fa;}} .page{{background:white; padding:18px; margin:0 auto 22px; box-shadow:0 3px 15px #d2dae0;}} }}
"""

def rpt_html(year, rows):
    cover=f"""<section class="page cover">
<div class="status">DRAF STAGING — BUKAN BAHAN PENGGUNA</div>
<div class="title">RPT RBT {year}<br>2027</div>
<h2>Reka Bentuk dan Teknologi • Tahun {year}</h2>
<p>32 PdP cadangan berdasarkan 32 jam minimum DSKP KSSR (Semakan 2017).</p>
<p>Kumpulan A dan B: tarikh ditetapkan selepas padanan takwim dan cuti negeri.</p>
<p>Nama sekolah: __________________________________________</p>
<p>Nama guru: _____________________________________________</p>
<p class="muted">RPT CikguLaju • untuk semakan — belum FINAL READY</p>
</section>"""
    data=[]
    for row in rows:
        data.append("<tr>"+"".join(f"<td>{h(row.get(col,''))}</td>" for col in
            ("PdP","Unit","Tajuk PdP","SK","SP","Rujukan Buku Teks m/s","Status"))+"</tr>")
    table=f"""<section>
<div class="header"><h1>RPT RBT Tahun {year} • 2027</h1>
<small>Susunan PdP cadangan; bukan minggu rasmi KPM • semua rujukan buku teks perlu disahkan</small></div>
<table><thead><tr><th>PdP</th><th>Unit</th><th>Fokus PdP</th><th>SK</th><th>SP</th><th>BT m/s</th><th>Status</th></tr></thead>
<tbody>{''.join(data)}</tbody></table>
<p class="notes">RPH dipadankan menggunakan ID unik. Tarikh kumpulan A/B, cuti negeri dan minggu sebenar belum ditentukan.
Jangan aktifkan bahan ini untuk guru sebelum semakan muka surat, aktiviti dan output natif selesai.</p></section>"""
    return "<!doctype html><html lang='ms'><head><meta charset='utf-8'><title>RPT RBT "+str(year)+" 2027 — DRAF</title><style>"+css(False)+"</style></head><body>"+cover+table+"</body></html>"

def rph_html(year, lessons):
    cards=[]
    for l in lessons:
        steps=[]
        for k,label in [("set_induksi","Set Induksi"),("aktiviti_1","Aktiviti 1"),("aktiviti_2","Aktiviti 2"),("pengukuhan_penilaian","Penilaian / Pengukuhan"),("penutup","Penutup")]:
            d=l["langkah"][k]
            steps.append(f"<tr><td style='width:20%'><b>{label}</b><br><small>{int(d['minit'])} minit</small></td><td>{h(d['aktiviti'])}</td></tr>")
        ref=l["rujukan_buku_teks"]
        pages=ref.get("calon_muka_surat_teks_digital")
        printed=", ".join(map(str,pages)) if pages else "Belum dipadankan"
        if pages: printed+=" (calon teks sahaja)"
        card=f"""<section class="page rph">
<div class="header"><div class="status">DRAF — BELUM DILULUSKAN</div>
<h1>RPH RBT Tahun {year} • {h(l["id"])}</h1>
<p><b>{h(l["unit_label"])}</b> — {h(l["tajuk"])}</p>
<small>Tarikh: ___________ Kelas: ___________ Masa: ___________ Tempoh: 60 minit</small>
</div>
<table class="main"><tbody>
<tr><th style="width:20%">SK / SP</th><td>{h(" / ".join(l["sk"]))} | {h(" / ".join(l["sp_codes"]))}</td></tr>
<tr><th>Objektif</th><td>{h(l["objektif"])}</td></tr>
<tr><th>Kriteria kejayaan</th><td>{h(l["kriteria_kejayaan"])}</td></tr>
<tr><th>BBM</th><td>{h(l["bbm"])}</td></tr>
<tr><th>Buku Teks</th><td>{h(printed)} — halaman belum diluluskan secara visual</td></tr>
</tbody></table>
<table><thead><tr><th>Fasa</th><th>Tindakan guru dan murid</th></tr></thead><tbody>{''.join(steps)}</tbody></table>
<div class="notes"><b>PBD:</b> {h(l["rubrik_pbd_khusus"])}<br>
<b>Keselamatan:</b> {h(l["keselamatan"])}<br>
<b>Refleksi guru:</b> _____ / _____ murid mencapai objektif. Tindakan susulan: ______________________</div>
</section>"""
        cards.append(card)
    return "<!doctype html><html lang='ms'><head><meta charset='utf-8'><title>RPH RBT "+str(year)+" 2027 — DRAF</title><style>"+css(True)+"</style></head><body>"+''.join(cards)+"</body></html>"

def render(year,out):
    base=ROOT/"rpt_2027"/"rbt"
    with (base/f"RPT_RBT_T{year}_2027_DRAF.csv").open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    source=ROOT/f"rph_standalone/rbt/tahun_{year}/RPH_RBT_T{year}_2027_DRAF.json"
    data=json.loads(source.read_text(encoding="utf-8"))
    lessons=data["pelajaran"]
    assert data["status"]=="DRAF_STAGING" and all(l["review"]["release_ready"] is False for l in lessons)
    assert len(lessons)==len(rows)==32
    rpt=out/f"RPT_RBT_T{year}_2027_DRAF_PREVIEW.html"
    rph=out/f"RPH_RBT_T{year}_2027_DRAF_PREVIEW.html"
    rpt.write_text(rpt_html(year,rows),encoding="utf-8")
    rph.write_text(rph_html(year,lessons),encoding="utf-8")
    print(f"PREVIEW T{year}: {rpt.name}, {rph.name} • 32 PdP • DRAF locked")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--year",default="all",choices=("all","4","5","6"))
    ap.add_argument("--out",type=Path,default=ROOT/"staging/rbt_2027_previews")
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    for year in (4,5,6) if args.year=="all" else (int(args.year),):
        render(year,args.out)

if __name__=="__main__":
    main()
