#!/usr/bin/env python3
"""Read-only consistency test for staged 96h Moral planning; not a release gate."""
from pathlib import Path
import csv, json
ROOT=Path(__file__).resolve().parents[1]

def main():
    totals={"core":0,"extra":0,"slots":0}
    for year in range(2,7):
        path=ROOT/f"rpt_2027/pendidikan_moral/year{year}_96h_coverage_PLANNING.csv"
        rows=list(csv.DictReader(path.open(encoding="utf-8",newline="")))
        cw=json.loads((ROOT/f"rpt_2027/pendidikan_moral/year{year}_crosswalk_DSKP.json").read_text(encoding="utf-8"))["units"]
        assert len(rows)==96,(year,len(rows))
        assert [r["Sesi_1_96"] for r in rows]==[f"{i:03d}" for i in range(1,97)],year
        assert {r["Tahun"] for r in rows}=={str(year)}
        core=[r for r in rows if r["Modul"]=="TERAS"]
        extra=[r for r in rows if r["Modul"]=="PENGUKUHAN"]
        assert len(core)==42 and len(extra)==54,(year,len(core),len(extra))
        assert [r["PdP_Teras_Asal"] for r in core]==[f"{i:03d}" for i in range(1,43)],year
        assert sum(int(r["Tempoh_Minit"]) for r in rows)==96*60,year
        for r in rows:
            u=cw[int(r["Unit"])-1]
            codes=[x["code"] for x in u["sp"]]
            assert r["SK"]==u["sk"] and all(s in codes for s in r["SP"].split("; ")),(year,r)
            assert not r["Tarikh_Kumpulan_A"] and not r["Tarikh_Kumpulan_B"],year
            assert "READY" not in r["Status_Dalaman"],year
        for r in core:
            assert (ROOT/r["Rujukan_RPH_Sedia_Ada"]).is_file(),(year,r["Rujukan_RPH_Sedia_Ada"])
            assert r["Status_Dalaman"]=="RPH_TERSEDIA_BETA80"
        for r in extra:
            assert not r["Rujukan_RPH_Sedia_Ada"] and r["Status_Dalaman"]=="PERLU_RPH_DAN_SEMAKAN_BUKU"
        for k,v in (("core",42),("extra",54),("slots",96)):
            totals[k]+=v
        print(f"Tahun {year}: 42 core + 54 pending extension = 96 x 60-min planning slots")
    assert totals=={"core":210,"extra":270,"slots":480},totals
    print("PASS planning integrity:",totals,"; NO claim of lesson, textbook or 2027 calendar readiness")
if __name__=="__main__":
    main()
