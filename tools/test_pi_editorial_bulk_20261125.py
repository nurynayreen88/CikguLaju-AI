"""Fast integration check: use real native state/rows for every bulk candidate, no PDF rerender."""
import os
import sqlite3
from collections import Counter
from tools.bm_native_v26_navigation_audit import database
from web.pi_editorial_bulk_20261125 import load_catalog, apply, norm, install
from pathlib import Path
from docx import Document
import fitz
import uuid
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
            if (item.get("final_review_fields") or {}).get("sp_text_proposal"):
                allowed.add("STANDARD PEMBELAJARAN")
                for code,description in item["final_review_fields"]["sp_text_proposal"].items():
                    assert jawi_display_digits(code+" "+description) in revised["STANDARD PEMBELAJARAN"]
            if item.get("corrected_objective"):
                key="OBJEKTIF PEMBELAJARAN" if "OBJEKTIF PEMBELAJARAN" in old else "OBJEKTIF"
                allowed.add(key)
                if item.get("corrected_sk_text"):
                    sk_keys=[k for k,v in revised.items() if norm(v)==norm(item["corrected_sk_text"])]
                    assert len(sk_keys)==1
                    allowed.update(sk_keys)
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
        assert sum(counts.values())==len(catalog)==696
        os.environ["CIKGULAJU_PI_EDITORIAL_BULK"]="1"
        assert install(runtime)
        for item in catalog.values():
            if item["id"] not in (1445,1533,1669,1599,1627,1751,1815):
                continue
            state=_native_state(runtime,{"year":item["year"],"subject":"PI","unit":item["unit"],"lesson":item["id"]},{"class":"","date":"","time":"","students":"","reflection":""})
            native=_native_text(runtime,state)
            uid="pifinal_"+uuid.uuid4().hex[:16]
            word=Path(runtime.create_word_file(state,native,uid))
            pdf=Path(runtime.create_pdf_file(state,native,uid+"p"))
            try:
                document=Document(str(word))
                whole=norm("\n".join(c.text for t in document.tables for row in t.rows for c in row.cells))
                for title,body in item["activities"]:
                    assert norm(title) in whole and norm(body) in whole,(item["id"],"activity missing")
                for key in ("corrected_objective","corrected_success_criteria","corrected_auto_reflection","corrected_sk_text"):
                    if item.get(key):
                        assert norm(item[key]) in whole,(item["id"],key,"not printed")
                if item.get("original_sk_text"):
                    assert norm(item["original_sk_text"]) not in whole
                with fitz.open(str(pdf)) as rendered:
                    assert len(rendered)==1
                    assert abs(rendered[0].rect.width-595.3)<2 and abs(rendered[0].rect.height-841.9)<2
                print("PI_FINAL_REAL_RENDER",item["id"],"PASS",flush=True)
            finally:
                word.unlink(missing_ok=True)
                pdf.unlink(missing_ok=True)
    finally:
        tmp.cleanup()

if __name__=="__main__":
    main()
