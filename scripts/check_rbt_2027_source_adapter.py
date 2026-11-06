#!/usr/bin/env python3
"""Non-production RBT source adapter verification."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from web.rbt_2027_staging_source import (
    RBTSourceUnavailable,approved_download_payload,
    internal_review,menu_pdp,menu_units,source_fingerprint,
)
def run():
    count=0
    for y in (4,5,6):
        all_pdp=[]
        units=menu_units(y)
        assert units and len({unit for unit,label in units})==len(units)
        for unit,label in units:
            assert label.startswith(f"Unit {unit}: ")
            pairs=menu_pdp(y,unit)
            assert pairs and len(set(p for p,label in pairs))==len(pairs)
            all_pdp.extend(x[0] for x in pairs)
        assert all_pdp==list(range(1,33)),(y,all_pdp)
        digests=[]
        for pdp in range(1,33):
            r=internal_review(y,pdp)
            assert r["id"]==f"RBT-T{y}-PDP-{pdp:03d}"
            assert r["review"]["release_ready"] is False
            assert all(r["rujukan_buku_teks"].get("calon_muka_surat_teks_digital",[]))
            digest=source_fingerprint(y,pdp)
            assert len(digest)==64 and digest!=source_fingerprint(y,max(1,pdp-1)) if pdp>1 else len(digest)==64
            digests.append(digest)
            for fmt in ("word","pdf"):
                try:approved_download_payload(y,pdp,fmt)
                except RBTSourceUnavailable as exc:
                    assert "belum dibuka" in str(exc)
                else:
                    raise AssertionError(f"PUBLIC EXPORT ESCAPED DRAFT GATE: {y},{pdp},{fmt}")
            count+=1
        assert len(set(digests))==32
    assert count==96
    print("PASS: 96 RBT dropdown PdP, source fingerprints unique per lesson, public exports denied.")
if __name__=="__main__":run()
