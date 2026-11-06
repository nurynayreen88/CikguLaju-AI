#!/usr/bin/env python3
"""Offline read-only integrity gate for BA RPT2027 *undated* A/B candidate crosswalk."""
import csv
import json
from collections import Counter
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
RPT = BASE / "rpt_2027" / "bahasa_arab"
EXPECTED = {2:60, 3:60, 4:58, 5:60, 6:60}
def rows(p):
    with p.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def main():
    meta = json.loads((RPT/"kalendar_2027_A_B_rujukan_DRAF.json").read_text(encoding="utf-8"))
    assert meta["release_authorized"] is False and meta["rpt_final_ready"] is False
    sources = [RPT/"pdp_001_012_DRAF.csv", *sorted(RPT.glob("year[2-6]_*.csv"))]
    originals = {}
    for p in sources:
        if not p.name.endswith("_DRAF.csv"): continue
        for row in rows(p):
            key=(row["tahun"],row["pdp"])
            assert key not in originals, f"duplicate source: {key}"
            originals[key]=row
    assert len(originals)==298
    counts=Counter(int(k[0]) for k in originals)
    assert dict(sorted(counts.items()))==EXPECTED, counts
    for group in ("A","B"):
        path=RPT/f"rpt_2027_KUMPULAN_{group}_INDEKS_PDP_DRAF.csv"
        result=rows(path); assert len(result)==298
        keys=set()
        for r in result:
            key=(r["tahun"],r["pdp"]); assert key not in keys; keys.add(key)
            original=originals[key]
            assert r["kumpulan"]==group and r["unit"]==original["unit"]
            assert r["sp"]==original["sp"] and r["sk"]==original["sk"] and r["fokus"]==original["fokus"]
            assert r["halaman_buku"]==original.get("halaman_buku_teks_dicadang","")
            assert r["ready"]=="FALSE" and r["kelulusan_guru"]=="FALSE"
            assert r["status_rpt"]=="DRAF_TARIKH_BELUM_DISAHKAN"
            assert not r["tarikh_pdp_2027"] and not r["waktu_mula"] and not r["waktu_tamat"] and not r["negeri"]
            f=BASE/r["rph_staging"]; assert f.is_file(), f
            src=f.read_text(encoding="utf-8")
            assert r["sp"] in src and "BELUM READY" in src
        assert keys==set(originals)
    print("PASS: 298 unique source IDs x Group A/B = 596 entries; no duplicates/orphans, no invented dates, 0 READY")
    print("BLOCKED: KPM/state holiday audit, period quota, RPT2027 actual dates, teacher per-PdP approval and runtime parity")
if __name__=="__main__": main()
