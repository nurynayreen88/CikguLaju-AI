"""Source-locked full SK topic and SP statements for 83 Science Year 5 drafts.

Educational DSKP text was transcribed from the owner's original 2019
KSSR Semakan 2017 PDF. This is curriculum metadata, not a teacher/panitia
signoff and not permission to redistribute any textbook PDF.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"audits/sains_y5_kssr2017_83_official_sp_statements_20261107.json"
SOURCE_SHA="e90744b28e6cc3943e8707475a911238ffc8b6a9dffb812bf742d35bcaa61ef6"
GROUPS={
    "2.1":5,"2.2":4,"2.3":4,"3.1":6,"3.2":4,"3.3":7,
    "4.1":3,"4.2":4,"5.1":1,"5.2":7,"5.3":4,
    "6.1":7,"7.1":6,"8.1":5,"8.2":4,
    "9.1":4,"9.2":3,"10.1":5,
}

def checked_statements():
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    if (
        data.get("source_sha256")!=SOURCE_SHA
        or data.get("source_file_id")!="1YkiK-pVo4UUzyOUvv_Vrico58eQyddCz"
        or data.get("source_pdf_pages")!=88
        or data.get("official_content_sp_count")!=83
        or data.get("official_kps_sp_count")!=12
        or data.get("sk_group_count")!=18
        or data.get("semantic_pedagogy_teacher_approval") is not False
        or data.get("ready_for_live") is not False
    ):
        raise ValueError("Unexpected Year5 DSKP edition or false academic approval")
    items=data.get("items",{})
    expected={f"{sk}.{i}" for sk,n in GROUPS.items() for i in range(1,n+1)}
    if set(items)!=expected or len(items)!=83:
        raise ValueError("Year5 official content statements missing or extra SP")
    for sp,row in items.items():
        if (
            row.get("sk")!=sp.rsplit(".",1)[0]
            or not isinstance(row.get("sk_title"),str)
            or len(row["sk_title"])<4
            or not isinstance(row.get("sp_text"),str)
            or not row["sp_text"].endswith(".")
            or not (20<=len(row["sp_text"])<=280)
        ):
            raise ValueError("Year5 official SP text incomplete: "+sp)
    return items

if __name__=="__main__":
    rows=checked_statements()
    print(f"SAINS_Y5_DSKP: {len(rows)} official content SP full statements source-locked, teacher signoff HOLD")
