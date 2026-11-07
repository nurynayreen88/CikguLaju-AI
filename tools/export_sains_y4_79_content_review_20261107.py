"""Create a real per-SP Year4 Science 79-item teacher/panitia content-review docket.

Source-specific instructional text is quoted from existing frozen activity
bank; prompts are REVIEW QUESTIONS, not machine-made academic approval.
Immutable 79 PdP, textbook unit TOC only, 0 exact pages and 0 scores.
"""
from __future__ import annotations
import csv
import json

from tools.audit_sains_342_pdp_release_gate_20261106 import ROOT
from tools.render_sains_y4_79_rph_draf_20261107 import get_y4_records

OUT=ROOT/"build/sains_y4_79_subject_content_panitia_HOLD_20261107"
RISK_CHECKS={
 2:"Manusia: semak pergerakan pernafasan dan demonstrasi fizikal tanpa memaksa murid menahan nafas; lindungi data kesihatan/peribadi.",
 3:"Haiwan: semak model/imej dan pengelasan saintifik; jangan tangkap, sentuh atau mencederakan haiwan sebenar.",
 4:"Tumbuh-tumbuhan: semak penyiasatan fototropisme/fotosintesis sesuai usia; pemotongan/tumbuhan berduri hanya guru.",
 5:"Sifat cahaya: jangan halakan cahaya terang atau laser ke mata; semak lukisan arah sinar dan pemboleh ubah.",
 6:"Bunyi: kawal volum; tiada pendedahan bunyi kuat berulang; bezakan sumber bunyi dengan medium dan pantulan.",
 7:"Tenaga: elakkan soket elektrik/nyalaan/bahan panas; bezakan bentuk tenaga dan sumber boleh diperbaharui.",
 8:"Bahan: tiada ujian rasa, bahan tajam atau bahan kimia tidak selamat; semak sifat dan pilihan berdasarkan bukti.",
 9:"Bumi: tidak memanjat/menjatuhkan objek berat; gunakan model selamat bagi graviti dan pergerakan Bumi.",
 10:"Mesin: gunakan model tuas dan beban ringan; jaga jari daripada titik cubit/fulkrum; kenal pasti daya dan beban.",
}
ISSUES={
 2:"DSKP: semak proses biologi dan kriteria PBD tanpa mendedahkan data peribadi murid.",
 3:"DSKP: semak istilah klasifikasi haiwan, organ pernafasan dan ciri vertebrata secara khusus.",
 4:"DSKP: bezakan gerak balas tumbuhan dan hasil/keperluan fotosintesis.",
 5:"DSKP: semak pantulan, pembiasan, arah cahaya dan perubahan bayang-bayang melalui bukti.",
 6:"DSKP: bezakan getaran, perambatan, pantulan serta kesan bunyi.",
 7:"DSKP: semak sumber, bentuk, perubahan dan prinsip keabadian tenaga.",
 8:"DSKP: semak hubungan sumber asas, sifat bahan, pemilihan bahan dan kegunaannya.",
 9:"DSKP: semak graviti, putaran/peredarannya, tempoh, arah serta siang-malam.",
 10:"DSKP: semak mesin ringkas, hubungan daya/beban/fulkrum dan aplikasi dalam reka bentuk.",
}

def docket():
    rows=get_y4_records()
    if len(rows)!=79 or {x["textbook_toc_unit"] for x in rows}!=set(RISK_CHECKS):
        raise ValueError("Year4 academic docket source unit coverage changed")
    output=[]
    for row in rows:
        code=row["pdp_code"];unit=row["textbook_toc_unit"]
        for k in ("hook","teacher1","pupil1","teacher2","pupil2","pbd","safety","materials"):
            if not row[k] or len(row[k])<10:
                raise ValueError("Year4 source pedagogical field absent "+code+" "+k)
        output.append({
            "Tahun":4,
            "Kod PdP":code,
            "SK":row["sk"],
            "SP":row["sp"],
            "Unit":row["unit"],
            "Tajuk asal PdP":row["tajuk"],
            "Buku Teks — konteks isi kandungan sahaja":row["textbook_unit_toc_note"],
            "Muka surat tepat bagi SP":"BELUM DISAHKAN",
            "Set induksi / rangsangan":row["hook"],
            "Aktiviti 1 — tindakan guru":row["teacher1"],
            "Aktiviti 1 — bukti murid":row["pupil1"],
            "Aktiviti 2 — tindakan guru":row["teacher2"],
            "Aktiviti 2 — bukti murid":row["pupil2"],
            "Bukti PBD individu yang dicadangkan":row["pbd"],
            "BBM":row["materials"],
            "Etika dan langkah keselamatan dalam draf":row["safety"],
            "Soalan semakan konsep DSKP":ISSUES[unit],
            "Soalan semakan keselamatan":RISK_CHECKS[unit],
            "Semak kesesuaian objektif dan SP":"BELUM",
            "Semak aras murid Tahun 4":"BELUM",
            "Semak KPS/manipulatif":"BELUM",
            "Semak kebolehlaksanaan alat & masa":"BELUM",
            "Semak bukti PBD setiap murid":"BELUM",
            "Semak halaman BT asal pada imej":"BELUM",
            "Semak variasi pemulihan/pengayaan":"BELUM",
            "Keputusan semakan panitia":"HOLD — BELUM DILULUSKAN",
            "Skor akademik (0-100)":"",
            "Nama guru/panitia":"",
            "Tarikh":"",
            "Boleh diterbitkan ke Web–Telegram":False
        })
    if len(output)!=79 or len({r["Kod PdP"] for r in output})!=79:
        raise ValueError("Year4 academic docket missing/duplicate PdP")
    if any(r["Skor akademik (0-100)"] or r["Nama guru/panitia"] for r in output):
        raise ValueError("Never prepopulate academic approval")
    return output

def main():
    rows=docket()
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"SAINS_TAHUN4_79_PDP_SEMAKAN_KANDUNGAN_PANITIA_HOLD.csv"
    with path.open("w",newline="",encoding="utf-8-sig") as fp:
        writer=csv.DictWriter(fp,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    meta={
        "source_pdp":79,
        "source_specific_teacher_pupil_pbd_and_safety_review_rows":79,
        "unit_specific_safety_review_prompts":9,
        "exact_source_textbook_sp_pages_approved":0,
        "teacher_academic_signoffs":0,
        "scores_approved":0,
        "source_original_pdp_immutable":True,
        "ready_for_runtime":False,
        "status":"STAGING_HOLD",
        "review_csv":path.name
    }
    (OUT/"SAINS_T4_79_ACADEMIC_REVIEW_GATE_HOLD.json").write_text(
        json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_T4_79_PANITIA: 79 individual content/safety/PBD review rows, 0 academic approval, HOLD")

if __name__=="__main__":
    main()
