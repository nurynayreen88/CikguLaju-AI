"""Per-PdP stable content identity for Sejarah 2027 staging.

Unlike a whole-year JSON digest, approval of another lesson does not invalidate
this lesson. The embedded approved_source_fingerprint is excluded to avoid a
cryptographic fixed point; all other approvals, lesson fields and source facts
are still included. A fingerprint is never itself evidence of approval.
"""
from __future__ import annotations

import csv
from copy import deepcopy
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAX_BYTES=4_000_000
HASH_PLACEHOLDER="<approved hash excluded>"

def source_paths(year,pdp):
    if type(year) is not int or year not in (4,5,6) or type(pdp) is not int or not 1<=pdp<=36:
        return None
    return (
        f"rph_standalone/sejarah/tahun_{year}/RPH_SEJ-T{year}-PDP-{pdp:03d}.md",
        f"rph_standalone/sejarah/y{year}_2027_rph_DRAF.json",
        f"curriculum/sejarah/y{year}_dskp_crosswalk_DRAF.json",
        f"curriculum/sejarah/y{year}_buku_teks_unit_map_20261106.json",
        "curriculum/sejarah/kalender_sejarah_2027_kumpulan_a_b.json",
        f"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{year}_2027_A_B_DRAF.csv",
    )

def _canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")

def fingerprint(year,pdp,*,root=ROOT):
    paths=source_paths(year,pdp)
    if paths is None: return None
    base=Path(root).resolve()
    digest=sha256()
    try:
        for rel in paths:
            file=base/rel
            if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(base):
                return None
            if not 0<file.stat().st_size<=MAX_BYTES:
                return None
            raw=file.read_bytes()
            if rel==paths[1]:
                obj=json.loads(raw.decode("utf-8"))
                rows=obj["lessons"]
                if (len(rows)!=36 or obj["year"]!=year or obj["academic_year"]!=2027):
                    return None
                selected=deepcopy(rows[pdp-1])
                if selected.get("id")!=f"SEJ-T{year}-PDP-{pdp:03d}" or selected.get("num")!=pdp:
                    return None
                # Always create this canonical slot, even before sign-off.
                # Mutating this field must not mutate the digest itself.
                approval=selected["rph"].setdefault("release_signoff",{})
                if not isinstance(approval,dict): return None
                approval["approved_source_fingerprint"]=HASH_PLACEHOLDER
                raw=_canonical({"year":year,"academic_year":2027,"lesson":selected})
            elif rel==paths[-1]:
                reader=csv.DictReader(StringIO(raw.decode("utf-8-sig")))
                rows=list(reader)
                if (len(rows)!=36 or not reader.fieldnames
                    or rows[pdp-1].get("ID")!=f"SEJ-T{year}-PDP-{pdp:03d}"
                    or rows[pdp-1].get("PdP")!=str(pdp)):
                    return None
                raw=_canonical({"columns":reader.fieldnames,"pdp":rows[pdp-1]})
            digest.update(rel.encode("utf-8")+b"\x00"+raw+b"\x00")
    except (OSError,UnicodeError,ValueError,KeyError,TypeError,csv.Error,IndexError):
        return None
    return digest.hexdigest()
