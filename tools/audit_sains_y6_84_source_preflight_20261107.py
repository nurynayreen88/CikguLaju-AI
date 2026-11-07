"""Read-only preflight of 84 Sains Year6 PdP source rows, not lesson release.

Original author: KPM BPK DSKP Sains Tahun 6, September 2021.
Public text-copy reference:
https://beebeeclassroom.com/wp-content/uploads/2022/04/DSKP-KSSR-Semakan-2017-Sains-Tahun-6_ISBN_.pdf
School-hosted catalog:
https://sites.google.com/moe.gov.my/sdh-selangor/dskp-dokumen-standard-kurikulum-dan-pentaksiran/sains-sr
This audit verifies staging SOURCE IDENTITIES against a known code inventory,
not the full learning-standard semantics or teacher/textbook approval.
Never write DB, update a runtime, generate placeholder RPH, or imply 80%.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

from tools.audit_sains_342_pdp_release_gate_20261106 import ROOT, analyze

OUT=ROOT/"build/sains_y6_84_preflight_20261107"
GROUPS={
    "2.1":4,"2.2":6,"3.1":6,"4.1":4,"4.2":3,"5.1":7,
    "6.1":3,"6.2":5,"6.3":4,"7.1":5,"8.1":3,"8.2":7,
    "9.1":6,"10.1":5,"11.1":5,"12.1":7,"13.1":4,
}
EXPECTED_SP={f"{group}.{i}" for group,count in GROUPS.items()
             for i in range(1,count+1)}

RISK_NOTES={
    "2.1":"Biologi pembiakan manusia: gunakan rajah KPM sesuai umur dan hormati privasi murid",
    "2.2":"Sistem saraf: jangan uji rangsangan menyakitkan atau gejala murid",
    "3.1":"Mikroorganisma: tiada kultur mikroorganisma tidak diketahui atau makanan berkulat hidup",
    "4.1":"Interaksi haiwan: gunakan media bukannya haiwan berbahaya",
    "4.2":"Persaingan tumbuhan: kawal pemboleh ubah dan elak tanaman beracun",
    "5.1":"Pemuliharaan: semak status kepupusan spesies pada edisi sumber tepat",
    "6.1":"Daya: gunakan objek ringan dan selamat",
    "6.2":"Geseran: guna permukaan rendah risiko tanpa ujian di jalan raya",
    "6.3":"Tekanan udara: elakkan vakum kuat atau kaca boleh pecah",
    "7.1":"Kelajuan: catat jarak dan masa di ruang tertutup, unit mesti konsisten",
    "8.1":"Makanan rosak: guna gambar, bukan sampel berkulat beracun",
    "8.2":"Pengawetan: tiada pemprosesan makanan berisiko atau produk untuk dimakan tanpa kawalan",
    "9.1":"Bahan buangan: guna bahan contoh bersih, tiada sampah tajam/biologi",
    "10.1":"Gerhana: jangan melihat Matahari atau melakukan pemerhatian tanpa alat pelindung khusus",
    "11.1":"Galaksi: bezakan skala Sistem Suria dengan skala Bima Sakti",
    "12.1":"Kekuatan/kestabilan: model beban ringan, uji satu faktor pada satu masa",
    "13.1":"Teknologi: nilaikan manfaat dan risiko dengan sumber sebenar",
}
assert len(EXPECTED_SP)==84
assert set(RISK_NOTES)==set(GROUPS)

def preflight(rows):
    if len(rows)!=342:
        raise ValueError("Full staged science ledger must have 342 PdP")
    y6=[row for row in rows if row["tahun"]==6]
    if len(y6)!=84:
        raise ValueError(f"Expected 84 Year6 source PdP, got {len(y6)}")
    y6=sorted(y6,key=lambda r:int(r["pdp_number"]))
    if {r["sp"] for r in y6}!=EXPECTED_SP:
        missing=EXPECTED_SP-{r["sp"] for r in y6}
        extra={r["sp"] for r in y6}-EXPECTED_SP
        raise ValueError(f"Year6 SP inventory mismatch missing={missing} extra={extra}")
    counts=Counter()
    report=[]
    for i,row in enumerate(y6,1):
        sp=row["sp"]
        group=sp.rsplit(".",1)[0]
        if row["pdp_code"]!=f"SCI-Y6-PDP-{i:03d}" or int(row["pdp_number"])!=i:
            raise ValueError(f"Year6 source sequence duplicated/wrong at {i}")
        if row["sk"]!=group or not row["unit"] or not row["tajuk"]:
            raise ValueError(f"Year6 SK/SP/unit/title incomplete: {sp}")
        if row["keputusan"]!="HOLD":
            raise ValueError("Year6 source unexpectedly ready: "+sp)
        counts[group]+=1
        report.append({
            "year":6,"pdp_code":row["pdp_code"],"sp":sp,"sk":group,
            "unit":row["unit"],"source_title":row["tajuk"],
            "source_sp_token_inventory":"STAGING_CODE_PRESENT",
            "dskp_full_text_verification":"PENDING_EDITION_AND_SEMANTIC_REVIEW",
            "textbook_visual_page":"UNVERIFIED",
            "source_edition":"KPM_BPK_DSKP_TAHUN6_2021_PUBLIC_TEXT_COPY",
            "specific_rph":"AUTHORING_EXISTS_IN_STAGING__WORD_PDF_PRINT_GATE_SEPARATE",
            "priority_safety_review":RISK_NOTES[group],
            "academic_quality_percent":"",
            "teacher_approval":"MISSING",
            "release_decision":"HOLD",
        })
    if dict(counts)!=GROUPS:
        raise ValueError("Year6 SK group counts changed")
    return report

def main():
    rows, source=analyze()
    results=preflight(rows)
    if source["decision"]!="HOLD":
        raise RuntimeError("Year6 source release gate unexpectedly lifted")
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/"SAINS_YEAR6_84_STAGING_SOURCE_PREFLIGHT.csv").open(
            "w",encoding="utf-8-sig",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    (OUT/"SUMMARY_YEAR6_HOLD.json").write_text(json.dumps({
       "date":"2026-11-07",
       "year":6,
       "source_pdp":84,
       "sp_codes_unique":84,
       "dskp_source_url":
       "https://beebeeclassroom.com/wp-content/uploads/2022/04/DSKP-KSSR-Semakan-2017-Sains-Tahun-6_ISBN_.pdf",
       "dskp_edition":"KPM_BPK_2021",
       "dskp_full_semantic_review":False,
       "original_textbook_in_drive":"549MB_NOT_VISUALLY_REVIEWED",
       "original_textbook_page_verified":0,
       "source_specific_rph_authoring_rows_expected":84,
       "standalone_rph_print_verified_in_this_preflight":False,
       "full_print_check":"LATER_STAGE_OF_SAME_CI",
       "pbd_teacher_signoff":0,
       "quality_percent_certified":None,
       "source_in_2027_live_runtime_verified":False,
       "decision":"HOLD",
       "no_db_or_runtime_write":True,
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_YEAR6_PREFLIGHT: 84/84 staged SP codes unique; "
          "KPM 2021 text-copy identified; source authoring elsewhere; "
          "Word/PDF output verified in later CI stages; HOLD")

if __name__=="__main__":
    main()
