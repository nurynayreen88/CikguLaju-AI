"""Science Year6: 84 individually authored DRAF activities from September 2021 KPM DSKP.

The SP learning-standard semantics were checked against a text mirror of the
2021 edition; this is NOT proof of scanned textbook page, teacher approval,
school calendar, formal PBD TP, 2027 KP2027, or live runtime availability.

Read-only, fail-closed, no AI API, no DB updates.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from tools.audit_sains_y6_84_source_preflight_20261107 import GROUPS,EXPECTED_SP,RISK_NOTES

ROOT=Path(__file__).resolve().parents[1]
FILES=(
    ROOT/"web/sains_y6_draf_bank_part1_20261107.tsv",
    ROOT/"web/sains_y6_draf_bank_part2_20261107.tsv",
    ROOT/"web/sains_y6_draf_bank_part3_20261107.tsv",
)
FIELDS=("sp","hook","teacher1","pupil1","teacher2","pupil2","pbd","materials")

KPS_OVERRIDES={
    "3.1.4":"1.1.10 Mengawal pemboleh ubah; 1.1.11 Membuat hipotesis; 1.1.12 Mengeksperimen",
    "4.2.1":"1.1.10 Mengawal pemboleh ubah; 1.1.8 Mentafsir data",
    "6.2.3":"1.1.10 Mengawal pemboleh ubah; 1.1.12 Mengeksperimen",
    "7.1.2":"1.1.3 Mengukur; 1.1.10 Mengawal pemboleh ubah; 1.1.12 Mengeksperimen",
    "7.1.4":"1.1.9 Mendefinisi secara operasi; 1.1.3 Mengukur",
    "8.2.3":"1.1.12 Mengeksperimen; 1.1.8 Mentafsir data",
    "12.1.3":"1.1.10 Mengawal pemboleh ubah; 1.1.12 Mengeksperimen",
    "12.1.4":"1.1.10 Mengawal pemboleh ubah; 1.1.12 Mengeksperimen",
}
MEASURE={"6.3.2","7.1.1","7.1.3","7.1.5","12.1.7"}
CLASSIFY={"3.1.1","4.1.1","4.1.3","4.2.2","5.1.3","8.2.2","9.1.3"}
INFER={"2.1.3","2.2.4","5.1.5","5.1.6","6.2.4","7.1.5","10.1.3"}
SKILL_NAMES={"1.1.1":"Memerhati","1.1.2":"Mengelas","1.1.3":"Mengukur",
             "1.1.4":"Membuat inferens","1.1.8":"Mentafsir data"}

def kps_for(sp):
    if sp in KPS_OVERRIDES:
        return KPS_OVERRIDES[sp]+"; 1.1.6 Berkomunikasi (cadangan)"
    code=("1.1.3" if sp in MEASURE else
          "1.1.2" if sp in CLASSIFY else
          "1.1.4" if sp in INFER else "1.1.1")
    return f"{code} {SKILL_NAMES[code]}; 1.1.6 Berkomunikasi (cadangan)"

def _load():
    bank={}
    counts=Counter()
    for path in FILES:
        for no,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
            if not line.strip():
                continue
            parts=line.split("|")
            if len(parts)!=len(FIELDS):
                raise ValueError(f"Malformed Y6 authored SP row {path.name}:{no}")
            row=dict(zip(FIELDS,parts))
            sp=row["sp"]
            group=sp.rsplit(".",1)[0]
            if sp not in EXPECTED_SP or sp in bank or group not in RISK_NOTES:
                raise ValueError("Unknown, duplicated, or unsupported Year6 SP "+sp)
            if any(not v.strip() or len(v.strip())<12 for k,v in row.items() if k!="sp"):
                raise ValueError(f"Underdeveloped/blank authored Year6 activity {sp}")
            if row["teacher1"]==row["teacher2"] or row["pupil1"]==row["pupil2"]:
                raise ValueError("Duplicated Year6 main activity tasks "+sp)
            row["safety"]=RISK_NOTES[group]
            if group=="3.1":
                row["safety"]+="; hanya yis pembakar makanan bungkusan atau data/gambar sedia ada"
            elif group=="10.1":
                row["safety"]+="; JANGAN melihat Matahari secara terus atau cuba pemerhatian gerhana sebenar tanpa perlindungan bertauliah"
            elif group=="8.2":
                row["safety"]+="; hasil projek bukan untuk dimakan dan penyediaan makanan diawasi guru"
            elif group=="2.1":
                row["safety"]+="; guna istilah saintifik sesuai umur tanpa mendedahkan kisah peribadi murid"
            row["source_status"]="2021_DSKP_SEMANTIC_TEXT_REVIEWED__ACADEMIC_APPROVAL_PENDING"
            bank[sp]=row
            counts[group]+=1
    if set(bank)!=EXPECTED_SP or dict(counts)!=GROUPS or len(bank)!=84:
        raise ValueError(f"Year6 bank missing/spurious SP: missing={EXPECTED_SP-set(bank)} extra={set(bank)-EXPECTED_SP}, group counts={counts}")
    if len({r["pbd"] for r in bank.values()})!=84 or len({r["hook"] for r in bank.values()})!=84:
        raise ValueError("Year6 standalone lesson outlines are not distinct")
    return bank

BANK=_load()
