"""DRAFT Sains source-only canonical Unit navigation.

For preview/testing only until source approval; don't replace live Telegram
or Web source without explicit release flag and end-to-end QA. Groups multiple
SK (2.1, 2.2, ...) under a single numbered TEXTBOOK UNIT while retaining each
PdP ID and SK/SP. Never write to SQLite.
"""
from __future__ import annotations
import copy
import re
from collections import defaultdict

class ScienceUnitSourceConflict(ValueError):pass

# Exact year-6 chapter title is separately grounded; the other source label is
# the overall theme and must NOT become a competing "Unit 12" in teacher UI.
SOURCE_APPROVED_DISAMBIG={(6,12):"Kestabilan dan Kekuatan"}

def _name(value):
    title=str(value or "").strip()
    title=re.sub(r"\s*/\s*\d+(?:\.\d+)?(?:\s+.*)?$", "",title).strip()
    return title

def _unit_index(row):
    sk=str(row.get("sk_code") or "").strip()
    m=re.fullmatch(r"(1[0-3]|[1-9])\.\d{1,2}",sk)
    if not m:raise ScienceUnitSourceConflict("Missing official SK major")
    return int(m[1])

def canonical_science_year(rows, year:int, academic_year:int):
    if type(year) is not int or year not in range(1,7):
        raise ScienceUnitSourceConflict("Unsupported Year")
    if type(academic_year) is not int or academic_year<2026 or academic_year>2100:
        raise ScienceUnitSourceConflict("Invalid academic year")
    if year==1 and academic_year>=2027:
        raise ScienceUnitSourceConflict("KP2027 Year1 is Alam dan Manusia, not legacy Sains KSSR")
    data=list(rows)
    if not data:
        raise ScienceUnitSourceConflict("No source lessons")
    grouped=defaultdict(list)
    for r in data:
        if not isinstance(r,dict) or r.get("year_label")!=f"Tahun {year}" or r.get("subject")!="Sains":
            raise ScienceUnitSourceConflict("Mixed or malformed subject source")
        if not str(r.get("pdp_sequence_code") or "").strip():
            raise ScienceUnitSourceConflict("PdP has no original code")
        grouped[_unit_index(r)].append(r)
    title_map={}
    for unit,entries in grouped.items():
        names={_name(r.get("unit_title")) for r in entries}
        names.discard("")
        if not names:raise ScienceUnitSourceConflict("No Unit title from source")
        folded={n.casefold() for n in names}
        dis=SOURCE_APPROVED_DISAMBIG.get((year,unit))
        if dis:
            if dis not in names:
                raise ScienceUnitSourceConflict("Approved chapter title missing from source")
            title_map[unit]=dis
        elif len(folded)==1:
            title_map[unit]=sorted(names)[0]
        else:
            raise ScienceUnitSourceConflict("Conflicting textbook titles for Year "+str(year)+" Unit "+str(unit))
    output=[]
    for r in data:
        unit=_unit_index(r)
        new=copy.deepcopy(r)
        new["_raw_unit_code_audit"]=r.get("unit_code")
        new["_raw_unit_title_audit"]=r.get("unit_title")
        new["unit_code"]=""
        new["unit_title"]=f"Unit {unit}: {title_map[unit]}"
        output.append(new)
    unique_units=[("",f"Unit {unit}: {title_map[unit]}") for unit in sorted(grouped)]
    return output,unique_units
