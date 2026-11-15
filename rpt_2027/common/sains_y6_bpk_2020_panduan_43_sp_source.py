"""Source-only 2020 BPK Sains Tahun6 Panduan PdP activity-page evidence.

This guide contains selected exemplar activities, not the full official
2021 KSSR2017 DSKP and not evidence that any legacy RPH uses KPS.
Output is a mapping of 43 SP codes to 16 source sections, with three codes
having two different page references.
"""
from __future__ import annotations
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
INDEX=ROOT/"rpt_2027/sains/bpk2020_panduan_sains_t6_43_sp_16_section_source_index_20261108_DRAF.json"
OFFICIAL=ROOT/"rpt_2027/sains/kssr2017_t6_2021_secondary_mirror_sp_code_ranges_20261107_DRAF.json"
SHA="2f8b8a1893b35608c06423867f8f47d1a7dbae1f7e06f1d8437daf57dc24d909"
SOURCE="https://drive.google.com/file/d/1qRPVgOctotKt4n1Reg4l7nA6ZtbfBGYg/view"
STATUS="STAGING_BPK_2020_SAINS_Y6_PANDUAN_PDP_16_BLOCKS_43_UNIQUE_SP_SOURCES_NOT_DSKP_APPROVAL"

def source_index():
    p=json.loads(INDEX.read_text(encoding="utf-8"))
    if (p.get("status")!=STATUS or p.get("year")!=6
        or p.get("source_pdf_page_count")!=118
        or p.get("source_pdf_sha256")!=SHA
        or p.get("source_drive_url")!=SOURCE
        or p.get("unique_sp_codes")!=43 or p.get("activity_sections")!=16
        or p.get("original_2021_dskp_wording_signoffs")!=0
        or p.get("approval_for_2027") is not False
        or p.get("live_web_telegram_verified") is not False
        or p.get("production_db_writes")!=0):
        raise ValueError("Panduan source index or release safeguards changed")
    official=json.loads(OFFICIAL.read_text(encoding="utf-8"))
    if (official.get("official_sp_count")!=96
        or official.get("academic_release_approved") is not False
        or official.get("source_official_original_pdf_sha256") is not None):
        raise ValueError("Year6 DSKP original verification gate altered")
    codes={f"{sk}.{n}" for sk,limit in
           official["official_sp_codes_by_sk_max_suffix"].items()
           for n in range(1,limit+1)}
    sections=p.get("sections")
    if not isinstance(sections,list) or len(sections)!=16:
        raise ValueError("Expected 16 BPK 2020 activity sections")
    mapping=defaultdict(list)
    pages=[]
    count=0
    for item in sections:
        page=item.get("pdf_page")
        if type(page) is not int or not 7<=page<=114:
            raise ValueError("Invalid source page number")
        pages.append(page)
        if item.get("activity_plan_approved") is not False or item.get("original_rph_verified") is not False:
            raise ValueError("Activity example is not verified legacy RPH")
        if not item.get("theme_guide_label") or not item.get("kps_terms"):
            raise ValueError("BPK guide section missing KPS and topic note")
        for sp in item["sp_codes"]:
            if not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{1,2}",sp) or sp not in codes:
                raise ValueError(f"Panduan includes non-DSKP2021 code {sp}")
            if any(r["pdf_page"]==page for r in mapping[sp]):
                raise ValueError("Duplicated source page for same SP")
            mapping[sp].append(dict(
                pdf_page=page,
                kps_terms=list(item["kps_terms"]),
                topic=item["theme_guide_label"],
                source_pdf_sha256=SHA,
                source_pdf_url=SOURCE,
                page_only_not_legacy_rph_verified=True
            ))
            count+=1
    if (len(mapping)!=43 or count!=46
        or pages!=sorted(pages)
        or {s for s,r in mapping.items() if len(r)>1}!={"2.2.3","6.3.1","6.3.2"}
        or set(mapping)&{f"1.1.{n}" for n in range(1,13)}):
        raise ValueError("2020 BPK source integrity, 43 unique SP / 46 page refs expected")
    return dict(mapping)
