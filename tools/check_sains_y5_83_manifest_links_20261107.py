"""Check actual 83-row Year5 RPH build manifest has safe external book sources.

Run only after rendering the 83 Word/PDF staging drafts. No live writes.
"""
from __future__ import annotations

import csv
from tools.render_sains_y5_83_rph_draf_20261107 import (
    OUT, BOOK_SOURCE_PARTS, BOOK_SOURCE_SHA, get_y5_records,
)
from tools.sains_y5_83_textbook_original_sp_pages_20261107 import (
    source_part_for_printed_page,
)


def checked():
    filename=OUT/"SAINS_Y5_83_MANIFEST_DRAF.csv"
    if not filename.is_file():
        raise ValueError("Missing Year5 rendered source manifest")
    with filename.open(encoding="utf-8-sig",newline="") as stream:
        rows=list(csv.DictReader(stream))
    source=get_y5_records()
    if len(rows)!=83 or len(source)!=83:
        raise ValueError("Not all 83 RPH are linked to original Year5 source")
    if len({r["pdp_code"] for r in rows})!=83:
        raise ValueError("Duplicate Year5 RPH textbook references")
    for actual,record in zip(rows,source):
        primary=record["textbook_page_primary"]
        part,zero_index=source_part_for_printed_page(primary)
        expected={
            "pdp_code":record["pdp_code"],"sp":record["sp"],
            "textbook_primary_page":str(primary),
            "textbook_primary_source_part":str(part),
            "textbook_primary_pdf_page_1_based":str(zero_index+1),
            "textbook_primary_external_source_url":BOOK_SOURCE_PARTS[part-1],
            "textbook_source_sha256_parts":";".join(BOOK_SOURCE_SHA),
            "textbook_sp_code_source_status":record["textbook_reference_status"],
            "academic_score":"NOT_CERTIFIED",
            "release":"HOLD",
        }
        for k,v in expected.items():
            if actual.get(k)!=v:
                raise ValueError("Year5 rendered source reference mismatch "+
                                 record["pdp_code"]+" / "+k)
    return rows


def main():
    rows=checked()
    print("SAINS_Y5_MANIFEST: 83/83 source book parts/printed/PDF pages "
          "match audited ledger; external links only; academic HOLD")


if __name__=="__main__":
    main()
