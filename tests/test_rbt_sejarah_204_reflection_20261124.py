"""All 204 source-bound rows; no actual teacher records or production access."""
import re
import copy
from web import rbt_2027_user_runtime as rbt
from web import sejarah_2027_user_runtime as sej

def test_204():
    totals = {}
    for module, count in ((rbt,32),(sej,36)):
        linked=0
        for year in (4,5,6):
            for pdp in range(1,count+1):
                row=module._lesson(year,pdp)
                assert row is not None,(module.SUBJECT,year,pdp)
                saved=copy.deepcopy(row)
                s=row if module is rbt else row["rph"]
                state={"subject":module.SUBJECT,"year":f"Tahun {year}","lesson_no":str(pdp),"sk_code":s["sk"][0] if module is rbt else s["sk"],"sp_code":s["sp_codes"][0],module.SELECTION:{"year":year,"pdp":pdp}}
                prior={"KELAS":"","TARIKH":"","MASA":"","BILANGAN MURID":""}
                out=module.adapt_rows(state,prior)
                assert all(out[k]==v for k,v in prior.items())
                assert not re.search(r"(?i)\bPdP\s+\d+",out["TAJUK"]),(year,pdp,out["TAJUK"])
                assert out["STANDARD KANDUNGAN"] and out["STANDARD PEMBELAJARAN"]
                assert "Aktiviti 1\n" in out["AKTIVITI UTAMA"] and "Aktiviti 2\n" in out["AKTIVITI UTAMA"]
                if module is rbt:
                    assert out["OBJEKTIF PEMBELAJARAN"]==s["objektif"]
                    assert out["KRITERIA KEJAYAAN"]==s["kriteria_kejayaan"]
                    assert all(s["langkah"][k]["aktiviti"] in out["AKTIVITI UTAMA"] for k in ("aktiviti_1","aktiviti_2","pengukuhan_penilaian"))
                    criterion=s["kriteria_kejayaan"]
                    objectives=[s["objektif"]]
                else:
                    assert out["OBJEKTIF PEMBELAJARAN"]=="; ".join(s["objective"])
                    assert out["KRITERIA KEJAYAAN"]==s["success_criteria"]
                    assert all(s[k]["activity"] in out["AKTIVITI UTAMA"] for k in ("aktiviti_1","aktiviti_2","pengukuhan_pbd"))
                    criterion=s["success_criteria"]
                    objectives=s["objective"]
                if "mencapai sasaran:" in out["REFLEKSI"]:
                    assert any(" ".join(x.split()).rstrip(".") in out["REFLEKSI"] for x in [criterion,*objectives])
                    linked+=1
                manual=module.adapt_rows({**state,"rph_teacher_reflection":"Catatan guru."},prior)
                assert manual["REFLEKSI"]=="Catatan guru."
                assert row==saved
        totals[module.SUBJECT]=(count*3,linked)
    print("SOURCE QA 204:",totals)
    assert sum(x[0] for x in totals.values())==204
