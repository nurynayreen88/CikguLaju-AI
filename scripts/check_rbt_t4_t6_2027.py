#!/usr/bin/env python3
"""Audit fail-closed RBT 2027 staging data; independent of Telegram/Web runtime."""
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {4: (57, [3,7,4,5,5,8]), 5:(34,[6,6,12,8]), 6:(23,[10,10,12])}
def check():
    total=0
    for year,(sp_count,module_hours) in EXPECTED.items():
        path=ROOT/f"rph_standalone/rbt/tahun_{year}/RPH_RBT_T{year}_2027_DRAF.json"
        data=json.loads(path.read_text(encoding="utf-8"))
        entries=data["pelajaran"]; assert len(entries)==32,(year,len(entries))
        assert sum(m["jam_dskp"] for m in data["modul"])==32
        assert [m["jam_dskp"] for m in data["modul"]]==module_hours
        assert data["status"]=="DRAF_STAGING" and data["bukan_modul_pengguna"] is True
        assert [e["pdp"] for e in entries]==list(range(1,33))
        assert len({e["id"] for e in entries})==32
        all_sp={code for e in entries for code in e["sp_codes"]}
        assert len(all_sp)==sp_count,(year,len(all_sp),sp_count)
        for entry in entries:
            assert entry["review"]["status"]=="DRAF"
            assert entry["review"]["release_ready"] is False
            assert entry["rujukan_buku_teks"]["muka_surat"] is None
            assert entry["rujukan_buku_teks"]["status"]=="BELUM_SAH_HALAMAN"
            assert sum(v["minit"] for v in entry["langkah"].values())==60
            assert all(k.startswith(entry["sk"][0]) or k.split(".")[:2] in [x.split(".") for x in entry["sk"]] for k in entry["sp_codes"])
        csv_path=ROOT/f"rpt_2027/rbt/RPT_RBT_T{year}_2027_DRAF.csv"
        assert len(csv_path.read_text(encoding="utf-8").splitlines())==33
        print(f"RBT Tahun {year}: 32 PdP; {len(all_sp)} kod SP; 32 jam; DRAF terkunci.")
        total+=len(entries)
    assert total==96
    print("PASS: 96 PdP data sahaja; TIADA kelulusan bahan untuk produksi.")
if __name__=="__main__":check()
