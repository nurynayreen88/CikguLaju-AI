"""Fast integration check: use real native state/rows for every bulk candidate, no PDF rerender."""
import os
import sqlite3
from collections import Counter
from tools.bm_native_v26_navigation_audit import database
from web.pi_editorial_bulk_20261125 import load_catalog, apply
from web.rph_pi_jawi_numerals_20261124 import jawi_display_digits

def main():
    os.environ["CIKGULAJU_PI_EDITORIAL_BULK"]="0"
    from tools import run_telegram_with_curriculum_api as running
    from web.telegram_verified_rpt_rph_bridge import _native_state,_native_text
    runtime=running.telegram_runtime
    catalog=load_catalog()
    tmp,db=database()
    try:
        runtime.DB_PATH=str(db)
        runtime.CIKGULAJU_DB_V2600_ACTIVE=True
        counts=Counter()
        failures=[]
        for item in catalog.values():
            state=_native_state(runtime,{"year":item["year"],"subject":"PI","unit":item["unit"],"lesson":item["id"]},{"class":"","date":"","time":"","students":"","reflection":""})
            native=_native_text(runtime,state)
            old=runtime._rph_rows(state,native)
            revised=apply(state,old,catalog)
            expected=jawi_display_digits("\n".join(f"اکتيۏيتي {i} - {title}\n1. {body}" for i,(title,body) in enumerate(item["activities"],1)))
            if revised.get("AKTIVITI UTAMA")!=expected:
                failures.append((item["id"],item["year"],item["pdp"],state.get("pdp_no"),state.get("lesson_no"),state.get("lesson")))
                continue
            allowed={"AKTIVITI UTAMA","KRITERIA KEJAYAAN","PENTAKSIRAN","REFLEKSI"}
            if item.get("corrected_objective"):
                key="OBJEKTIF PEMBELAJARAN" if "OBJEKTIF PEMBELAJARAN" in old else "OBJEKTIF"
                allowed.add(key)
                assert revised[key]==jawi_display_digits(item["corrected_objective"])
                assert revised["KRITERIA KEJAYAAN"]==jawi_display_digits(item["corrected_success_criteria"])
            assert {k:v for k,v in old.items() if k not in allowed}=={k:v for k,v in revised.items() if k not in allowed}
            manual={**state,"rph_teacher_reflection":"Catatan guru","rph_reflection_mode":"manual"}
            assert apply(manual,old,catalog)["REFLEKSI"]==old["REFLEKSI"]
            wrong={**state,"subject":"Matematik"}
            assert apply(wrong,old,catalog) is old
            counts[item["year"]]+=1
        print("PI_BULK_INTEGRATION",dict(counts),"total",sum(counts.values()),"catalog",len(catalog),flush=True)
        assert not failures, failures
        assert sum(counts.values())==len(catalog)==685
    finally:
        tmp.cleanup()

if __name__=="__main__":
    main()
