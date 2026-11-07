"""84 Year6 source-specific human academic review rows, not auto-grading.

Year6 teacher/Panitia must approve DSKP semantics, KPS, textbook SP pages
and actual PBD/safety. This reviewer does not modify DB or runtime.
"""
from __future__ import annotations
import csv
import json

from tools.audit_sains_342_pdp_release_gate_20261106 import ROOT
from tools.audit_sains_y6_84_source_preflight_20261107 import RISK_NOTES,GROUPS
from tools.render_sains_y6_84_rph_draf_20261107 import get_y6_records

OUT=ROOT/"build/sains_y6_84_subject_content_panitia_HOLD_20261107"

def docket():
    source=get_y6_records()
    if len(source)!=84 or len(RISK_NOTES)!=17:
        raise ValueError("Source Year6 84 distinct PdP / 17 skills changed")
    output=[]
    for r in source:
        code=r["pdp_code"];sp=r["sp"];sk=r["sk"]
        if sk not in RISK_NOTES or not sp.startswith(sk+"."):
            raise ValueError("Invalid Year6 SP/group identity "+code)
        toc=r["textbook_toc_range"]
        if toc["exact_sp_page"] is not None or toc["teacher_signoff"] is not False:
            raise ValueError("Year6 fake textbook page approval "+code)
        for k in ("hook","teacher1","pupil1","teacher2","pupil2","pbd","materials"):
            if len(r[k])<12:
                raise ValueError("Year6 specific lesson draft missing "+code+" "+k)
        output.append({
            "Tahun":6,
            "Kod PdP":code,
            "SK":sk,
            "SP":sp,
            "Unit asal sumber":r["unit"],
            "Tajuk PdP asal":r["tajuk"],
            "Buku Teks — konteks BAB dari isi kandungan sahaja":
                f"{toc['unit']} / {toc['topic']} (m/s {toc['range_start']}-{toc['range_end']}, "
                "BUKAN pengesahan halaman SP)",
            "Muka surat tepat SP":"BELUM",
            "Set induksi":r["hook"],
            "Aktiviti 1 — Guru":r["teacher1"],
            "Aktiviti 1 — Murid":r["pupil1"],
            "Aktiviti 2 — Guru":r["teacher2"],
            "Aktiviti 2 — Murid":r["pupil2"],
            "Bukti PBD dicadangkan":r["pbd"],
            "BBM":r["materials"],
            "KPS cadangan":r["kps"],
            "Keselamatan spesifik topik — SEMAK":RISK_NOTES[sk],
            "Semak maksud penuh SP DSKP 2021":"BELUM",
            "Semak tahap murid Tahun 6":"BELUM",
            "Semak pemulihan/pengayaan":"BELUM",
            "Semak ketepatan model/rajah/alat":"BELUM",
            "Semak aktiviti praktikal dan peraturan sains":"BELUM",
            "Semak PBD individu & kriteria":"BELUM",
            "Semak kesesuaian buku teks muka surat tepat":"BELUM",
            "Semak kesepadanan RPT & jadual guru":"BELUM",
            "Keputusan panitia":"HOLD — GURU BELUM MELULUSKAN",
            "Skor kualiti akademik":"",
            "Pengesah panitia":"",
            "Tarikh pengesahan":"",
            "Siap untuk Web/Telegram":False
        })
    if len(output)!=84 or len({r["Kod PdP"] for r in output})!=84:
        raise ValueError("Year6 academic docket has missing/duplicate source PdP")
    if any(x["Pengesah panitia"] or x["Skor kualiti akademik"] for x in output):
        raise ValueError("Academic approval must never be fabricated")
    return output

def main():
    rows=docket()
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"SAINS_TAHUN6_84_SEMAKAN_AKADEMIK_PBD_KPS_HOLD.csv"
    with path.open("w",encoding="utf-8-sig",newline="") as fp:
        writer=csv.DictWriter(fp,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    report={
        "pdp_count":84,
        "individual_pbd_kps_safety_review_rows":84,
        "risk_groups_covered":17,
        "textbook_toc_topic_ranges_only":84,
        "textbook_exact_sp_page_approved":0,
        "academic_teacher_signoff":0,
        "academic_percent_certified":None,
        "same_original_source_pdp_ids":True,
        "production_or_db_writes":False,
        "ready_for_runtime":False,
        "status":"STAGING_HOLD"
    }
    (OUT/"SAINS_T6_84_PANITIA_REVIEW_GATE_HOLD.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_T6_84: individual KPS/PBD/activity/risk review queue 84/84, 17 topic risks, academic HOLD")

if __name__=="__main__":
    main()
