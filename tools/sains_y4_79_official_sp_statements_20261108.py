"""Validate 79 official Year4 KSSR2017 Science content-SP statements.

Extracted from the owner's original 2018 KPM DSKP PDF, not a textbook.
An exact-SP statement is curriculum evidence, NOT pedagogical approval.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"audits/sains_y4_79_official_dskp_sp_statements_20261108.json"

GROUPS={
    "2.1":6,"2.2":4,"2.3":5,"3.1":4,"3.2":4,"4.1":4,
    "4.2":5,"5.1":4,"5.2":4,"5.3":4,"6.1":5,
    "7.1":6,"7.2":3,"8.1":3,"8.2":4,"9.1":3,
    "9.2":4,"10.1":3,"10.2":4,
}

def checked_statements():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    if (data.get("subject")!="Sains" or data.get("year")!=4
        or data.get("source_id")!="1eXDdb_qSfCKyqoVtl9T4q2I4rKyHtk9D"
        or data.get("source_pdf")!="GuruBesar_DSKP_Sains_Tahun_4.pdf"
        or data.get("source_published_year")!=2018
        or data.get("curriculum")!="KSSR Semakan 2017"
        or data.get("source_sp_count")!=79
        or data.get("source_sk_count")!=19
        or data.get("kps_standards_separate_count")!=12
        or data.get("teacher_pedagogy_approved") is not False
        or data.get("book_exact_pages_verified") is not False
        or data.get("release_status")!="DRAF_HOLD"):
        raise ValueError("Sains Year4 official DSKP source edition or release status changed")
    expected={f"{group}.{i}" for group,n in GROUPS.items() for i in range(1,n+1)}
    items=data.get("items",{})
    if set(items)!=expected or len(items)!=79:
        raise ValueError("Year4 official SP coverage mismatch")
    for code,record in items.items():
        text=record.get("sp_text")
        if (record.get("sk")!=code.rsplit(".",1)[0]
            or record.get("source_kind")!="ORIGINAL_KPM_YEAR4_DSKP_EXTRACTED_TEXT"
            or not isinstance(record.get("source_text_character_offset"),int)
            or not isinstance(text,str) or not 23<=len(text)<=260
            or not text.endswith(".") or not re.match(
                r"^(Mengenal|Menjelas|Menyatakan|Memerihal|Membeza|Memberi|Menaakul|"
                r"Mengitlak|Mengelas|Membuat|Menjana|Mengeksperimen|Membanding|"
                r"Melukis|Menyenaraikan|Menghubung|Mereka|Menyelesaikan|Merumus)",text)):
            raise ValueError("Malformed/unverified DSKP SP text "+code)
    return items

if __name__=="__main__":
    print("SAINS_Y4_DSKP: 79 official content SP exact statements; "
          "academic/panitia and textbook pages HOLD",len(checked_statements()))
