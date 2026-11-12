"""Create five *reference-only* Science five-column SP registers, no fake 2027 RPT.

The canonical v26.00 DB stores authentic verified Science SK/SP text per Year,
but ONLY 2026 unit-level RPT entries, not confirmed 2027 PdP schedules.
Therefore this output is explicitly an SP/DSKP register PREVIEW, not a lesson
RPT, and it leaves all weeks and group dates unallocated.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import re
import sqlite3
from tempfile import TemporaryDirectory
from rpt_2027.common.format_2026_layout_preview import build_preview,validate_rows

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_dskp_index_BUKAN_RPT"
PARTS=("v26_00_part1.bin","v26_00_part2.bin","v26_00_part3.bin")
SHA="b4c6914afb36747e51c2cb9d4234cf71063283ac31312e1ac235f0b955788ff6"
EXPECTED={2:31,3:30,4:110,5:107,6:109}


def science_source():
    with TemporaryDirectory(prefix="rpt2027_science_readonly_") as d:
        dest=Path(d)/"canonical.db"
        sha=hashlib.sha256()
        with dest.open("wb") as dst:
            for name in PARTS:
                with (ROOT/name).open("rb") as src:
                    while chunk:=src.read(1024*1024):
                        sha.update(chunk);dst.write(chunk)
        if sha.hexdigest()!=SHA:
            raise ValueError("Canonical split DB hash mismatches")
        conn=sqlite3.connect(f"file:{dest}?mode=ro&immutable=1",uri=True)
        records={}
        for year,count in EXPECTED.items():
            cur=conn.execute(
                "SELECT sk_code,sk_text,sp_code,sp_text,topic,subtopic,verified "
                "FROM curriculum_standards WHERE subject='Sains' AND year_label=?",
                (f"Tahun {year}",))
            rows=cur.fetchall()
            if len(rows)!=count or any(int(x[6])!=1 for x in rows):
                raise ValueError(f"Sains Y{year}: missing or unverified source DSKP rows")
            codes=[x[2] for x in rows]
            if len(set(codes))!=count:
                raise ValueError("Duplicated official Science SP within Year")
            def sort_key(v):
                c=v[2]
                if not re.fullmatch(r"\d+\.\d+\.\d+",c):
                    raise ValueError(f"Unexpected Science standard code {c}")
                return tuple(map(int,c.split(".")))
            rows=sorted(rows,key=sort_key)
            out=[]
            for i,(sk_code,sk_text,sp_code,sp_text,topic,subtopic,verified) in enumerate(rows,1):
                if not all(isinstance(s,str) and s.strip() for s in
                           (sk_code,sk_text,sp_code,sp_text,topic)):
                    raise ValueError(f"Sains Y{year} source row {i} incomplete")
                out.append({
                    "id":f"{i:03d}",
                    "display_id":f"DSKP SP {sp_code} — indeks, BUKAN PdP",
                    "week":"",
                    "unit":"Topik DSKP: "+topic.strip(),
                    "topic":"Subtopik: "+(subtopic or "").strip() if subtopic else
                            "Kod SP ini perlu diagih kepada PdP 2027 sebenar.",
                    "sk":sk_code,
                    "sp":sp_code,
                    "sk_display":sk_code+" — "+sk_text.strip(),
                    "sp_display":sp_code+" — "+sp_text.strip(),
                    "note":("INDEKS DSKP SAHAJA; BUKAN RPT PdP 2027. "
                            "Minggu/tarikh dan aktiviti PdP belum dirancang. "
                            "Sumber 2026 tidak boleh terus menggantikan 2027."),
                    "source_status":"DSKP_VERIFIED_IN_V26_00; RPT_2027_NOT_PLANNED",
                })
            validate_rows("sains",year,out)
            records[year]=out
        conn.close()
        return records


def build_all(destination=OUT):
    source=science_source()
    dest=Path(destination)
    products=[]
    for year,rows in source.items():
        file=dest/f"CIKGULAJU_SAINS_TAHUN_{year}_2027_INDEKS_DSKP_BUKAN_RPT_PDP_DRAF.pdf"
        build_preview("sains",year,rows,file)
        products.append((year,len(rows),file))
    if len(products)!=5 or sum(x[1] for x in products)!=387:
        raise ValueError("Science source indexing incomplete")
    return products


if __name__=="__main__":
    for y,n,p in build_all():
        print(f"SCIENCE_INDEX_SOURCE_ONLY Y{y} {n} verified standards, NOT a 2027 PdP RPT, {p}")
