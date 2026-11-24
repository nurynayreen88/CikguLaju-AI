"""Isolated dry-land Aquatics V2 adapter; not an enabled download route."""
from __future__ import annotations
import json
from pathlib import Path
from web.rph_unified_engine import render_structured_rph

SOURCE=Path(__file__).resolve().parents[1]/"rph_standalone/pjpk/akuatik_v2_darat_t1_t6_20261124.json"

def records():
    data=json.loads(SOURCE.read_text(encoding="utf-8"))
    if data["status"]!="QA_NOT_PUBLISHED" or len(data["records"])!=18:
        raise ValueError("Akuatik V2 source unavailable")
    return data["records"]

def resolve(year, source_id):
    if type(year) is not int or not isinstance(source_id,str):
        raise ValueError("Invalid Aquatics V2 selection")
    for r in records():
        if r["year"]==year and r["source_id"]==source_id and r["variant"]=="V2_DARAT" and r["ready"] is False:
            return r
    raise ValueError("Unknown Aquatics V2 selection")

def render(year, source_id, fmt, teacher=None):
    r=resolve(year,source_id)
    teacher=teacher or {}
    s=r["standard_descriptions"]
    heading=("Rancangan Pengajaran Harian","Pendidikan Jasmani · Tahun %d"%year,r["title"])
    details=[
        ("PdP",source_id),
        *[(label,str(teacher.get(key) or "")) for label,key in
          (("Kelas","class"),("Tarikh","date"),("Masa","time"),("Bilangan Murid","students"))],
        ("Bidang / Subbidang" if year==1 else "Standard Kandungan","; ".join(s["sk"])),
        ("Standard Pembelajaran","; ".join(s["psychomotor"]+s["cognitive"]+s["affective"])),
        ("Objektif Pembelajaran",r["objective"]),
        ("Kriteria Kejayaan",r["criteria"]),
        ("BBM",r["bbm"]),
        ("Keselamatan",r["safety"]),
        ("EMK / Nilai","Keselamatan, kerjasama dan tanggungjawab."),
        ("PAK21","Komunikasi dan pembelajaran kolaboratif."),
        ("PBD",r["pbd"]),
        ("Pemulihan / Pengayaan",r["remedial"]+" "+r["extension"]),
    ]
    # The original candidate activity text is kept in full; explicit teacher
    # and pupil roles from the source are not rewritten or reclassified.
    activities=[("Fasa","Guru","Murid"),
                ("Set Induksi",r["induction"],"Memerhati dan memberikan respons.")]
    for i,a in enumerate(r["activities"],1):
        if a["body"].startswith("Guru "):
            activities.append(("Aktiviti %d – %s"%(i,a["title"]),a["body"],"Mengikuti demonstrasi dan arahan keselamatan."))
        else:
            activities.append(("Aktiviti %d – %s"%(i,a["title"]),"Membimbing dan memerhati evidens murid.",a["body"]))
    activities.append(("Penutup","Merumuskan objektif dan evidens.",r["closure"]))
    reflection=[("Refleksi",r["reflection"])]
    return render_structured_rph(source="akuatik_v2",fmt=fmt,heading=heading,
        details=details,activities=activities,footer=reflection,compact=True,
        label_fill="E7F0E6")
