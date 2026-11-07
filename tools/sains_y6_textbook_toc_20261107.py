"""Science Year6 2021 DBP textbook TOC-only topic-range lookup.

TOC page spans are broad context, NOT verified teaching/SP/exercise pages.
Do not invent exact page matches or set academic/readiness flags.
"""
from __future__ import annotations
import json
from pathlib import Path

from tools.audit_sains_y6_84_source_preflight_20261107 import EXPECTED_SP,GROUPS
from tools.audit_sains_342_pdp_release_gate_20261106 import ROOT

PATH=ROOT/"audits/sains_y6_2021_textbook_toc_topic_ranges_20261107.json"
ISBN="978-983-49-3278-7"
SOURCE_URL="https://anyflip.com/mcde/elam/basic"

def load_toc_ranges():
    data=json.loads(PATH.read_text(encoding="utf-8"))
    if (data["year"]!=6 or data["edition"]!=2021 or data["isbn"]!=ISBN or
        data["source_url"]!=SOURCE_URL or
        data["exact_sp_page_verified"] is not False or
        data["teacher_approved"] is not False or
        data["no_runtime_update"] is not True):
        raise ValueError("Incorrect 2021 Year6 textbook TOC version or false verification")
    if set(data["groups"])!=set(GROUPS) or len(data["groups"])!=17:
        raise ValueError("Year6 TOC topic groups incomplete")
    last=0
    for key,row in data["groups"].items():
        if (row.get("lesson_page_assignment")!="PENDING" or
            row.get("confidence")!="TOPIC_OR_CHAPTER_RANGE_ONLY" or
            not row.get("unit") or not row.get("topic")):
            raise ValueError("No exact Year6 SP textbook page may be claimed: "+key)
        start,end=row["printed_topic_start"],row["printed_topic_end"]
        if not (isinstance(start,int) and isinstance(end,int) and
                13<=start<=end<=222 and start>last):
            raise ValueError("Year6 textbook TOC topic spans inconsistent: "+key)
        last=end
    if len(EXPECTED_SP)!=84:
        raise ValueError("Source 84 SP inventory changed")
    return data

def cue_for(sp):
    if sp not in EXPECTED_SP:
        raise ValueError("Wrong Year6 source SP: "+sp)
    doc=load_toc_ranges()
    key=sp.rsplit(".",1)[0]
    item=doc["groups"][key]
    return {
        "source":SOURCE_URL,
        "range_start":item["printed_topic_start"],
        "range_end":item["printed_topic_end"],
        "unit":item["unit"],
        "topic":item["topic"],
        "teacher_signoff":False,
        "exact_sp_page":None,
        "status":"UNIT_TOPIC_TOC_ONLY__EXACT_SP_TEXTBOOK_PAGE_PENDING"
    }

def short_cue(sp):
    c=cue_for(sp)
    return (f"Buku Teks Sains T6, tajuk '{c['topic']}', "
            f"julat m/s {c['range_start']}-{c['range_end']} menurut kandungan "
            "(bukan pengesahan halaman SP). DRAF/HOLD.")

if __name__=="__main__":
    d=load_toc_ranges()
    print("Y6_TEXTBOOK_TOC: 17 groups, 84 SP contexts, 0 individual SP page approvals; HOLD")
