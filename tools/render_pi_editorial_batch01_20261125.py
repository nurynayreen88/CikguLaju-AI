"""Render curated PI activity candidates on the actual native engine, QA only."""
from pathlib import Path
import json
import sqlite3
import uuid
import shutil
from tools.bm_native_v26_navigation_audit import database
from tools.audit_pi_active_activity_quality_20261125 import normalized
from web.rph_pi_jawi_numerals_20261124 import jawi_display_digits
from docx import Document
import fitz

def compare_word_layout(baseline, candidate, activity_titles, original_objective=None, corrected_objective=None):
    """Compare actual emitted DOCX structure and all non-activity cells."""
    assert len(baseline.tables)==len(candidate.tables)
    changed=[]
    for ti,(old_table,new_table) in enumerate(zip(baseline.tables,candidate.tables)):
        assert old_table._tbl.tblPr.xml==new_table._tbl.tblPr.xml, ("table properties",ti)
        assert old_table._tbl.tblGrid.xml==new_table._tbl.tblGrid.xml, ("table grid",ti)
        assert len(old_table.rows)==len(new_table.rows)
        for ri,(old_row,new_row) in enumerate(zip(old_table.rows,new_table.rows)):
            assert len(old_row.cells)==len(new_row.cells)
            for ci,(old_cell,new_cell) in enumerate(zip(old_row.cells,new_row.cells)):
                assert old_cell._tc.tcPr.xml==new_cell._tc.tcPr.xml, ("cell properties",ti,ri,ci)
                if normalized(old_cell.text)!=normalized(new_cell.text):
                    changed.append((ti,ri,ci))
                    activity_changed=all(normalized(title) in normalized(new_cell.text) for title in activity_titles)
                    objective_changed=bool(corrected_objective and normalized(original_objective) in normalized(old_cell.text) and normalized(corrected_objective) in normalized(new_cell.text))
                    assert activity_changed or objective_changed, ("unexpected changed cell",ti,ri,ci)
    assert changed, "No actual activity cell changed"
    return changed

def main():
    from tools import run_telegram_with_curriculum_api as running
    from web.telegram_verified_rpt_rph_bridge import _native_state,_native_text
    from web.pi_navigation import pi_navigation_unit
    runtime=running.telegram_runtime
    tmp,db=database()
    root=Path("qa/pi-editorial-batch01")
    root.mkdir(parents=True,exist_ok=True)
    records=[]
    for batch_file in sorted(Path("staging/pendidikan_islam").glob("active_activity_editorial_batch*_20261125.json")):
        batch=json.loads(batch_file.read_text(encoding="utf8"))
        assert batch["status"]=="QA_ONLY_NOT_FOR_RUNTIME"
        records.extend(batch["records"])
    assert len(records)>=128 and len({item["id"] for item in records})==len(records)
    objective_file=Path("staging/pendidikan_islam/active_activity_objective_corrections_20261125.json")
    objective_items=json.loads(objective_file.read_text(encoding="utf8"))["records"] if objective_file.exists() else []
    objective_ids={x["id"] for x in objective_items}
    assert len(objective_ids)==len(objective_items)
    records=[x for x in records if x["id"] not in objective_ids]
    corrected=[{**x,"objective":x["original_objective"],"source_note":x["original_source_note"]} for x in objective_items]
    # Test objective patches first, to detect failures before the full render.
    records=corrected+records
    assert len({x["id"] for x in records})==len(records)
    # Validate every draft before any expensive native render, so missing
    # teacher/pupil actions cannot halt a multi-hundred-document run late.
    failures=[]
    for item in records:
        tag=(item["year"],item["pdp"],item["id"])
        activities=item["activities"]
        if len(activities)!=3:
            failures.append((tag,"activity_count"))
        for idx,(title,body) in enumerate(activities,1):
            if "موريد" not in body:
                failures.append((tag,"missing_pupil",idx,title))
        if not any("ݢورو" in body for title,body in activities):
            failures.append((tag,"missing_teacher"))
    assert not failures, failures
    print("PI_EDITORIAL_PREFLIGHT",len(records),"passed",flush=True)
    payload={"records":records}
    original=runtime._rph_rows
    original_document=getattr(runtime,"_rph_document_rows",None)
    try:
        runtime.DB_PATH=str(db)
        runtime.CIKGULAJU_DB_V2600_ACTIVE=True
        reports=[]
        seen=set()
        for item in payload["records"]:
            assert item["status"] in ("EDITORIAL_QA_NOT_READY","OBJECTIVE_AND_ACTIVITY_QA_NOT_READY")
            corrected_objective=item.get("corrected_objective")
            if corrected_objective:
                assert normalized(corrected_objective)!=normalized(item["objective"])
            with sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True) as con:
                con.row_factory=sqlite3.Row
                source=dict(con.execute("SELECT * FROM rpt_entries WHERE id=? AND verified=1 AND subject='Pendidikan Islam'",(item["id"],)).fetchone())
            assert source["sequence_no"]==item["pdp"]
            assert source["year_label"]==f"Tahun {item['year']}"
            assert source["activity_note"]==item["source_note"]
            assert pi_navigation_unit(source)==item["unit"]
            state=_native_state(runtime,{"year":item["year"],"subject":"PI","unit":item["unit"],"lesson":item["id"]},
                {"class":"","date":"","time":"","students":"","reflection":""})
            native=_native_text(runtime,state)
            rows=original(state,native)
            assert normalized(rows.get("OBJEKTIF PEMBELAJARAN") or rows.get("OBJEKTIF"))==normalized(item["objective"])
            activity=jawi_display_digits("\n".join(f"اکتيۏيتي {i} - {title}\n1. {body}" for i,(title,body) in enumerate(item["activities"],1)))
            assert len(item["activities"])==3 and activity not in seen
            seen.add(activity)
            assert all("موريد" in body for title,body in item["activities"]), (item["year"],item["pdp"],"missing pupil action")
            assert "ݢورو" in activity
            assert len(activity)<=len(rows["AKTIVITI UTAMA"])+100, "Avoid unchecked long output"
            # Isolated single-record test. Render wrappers can copy or normalize
            # state, so validate the source via the exact original objective and
            # standard rather than requiring an internal ID field to survive.
            baseline_path=Path(runtime.create_word_file(state,native,"pi_baseline_"+uuid.uuid4().hex[:16]))
            baseline_document=Document(str(baseline_path))
            baseline_path.unlink(missing_ok=True)
            row_hits=[]
            expected_objective=normalized(rows.get("OBJEKTIF PEMBELAJARAN") or rows.get("OBJEKTIF"))
            expected_sp=normalized(rows.get("STANDARD PEMBELAJARAN"))
            def replace_activity(s,current,boundary):
                if not isinstance(current,dict):
                    return current
                objective_key="OBJEKTIF PEMBELAJARAN" if "OBJEKTIF PEMBELAJARAN" in current else "OBJEKTIF"
                same_objective=normalized(current.get(objective_key)) in ({expected_objective,normalized(corrected_objective)} if corrected_objective else {expected_objective})
                same_sp=normalized(current.get("STANDARD PEMBELAJARAN"))==expected_sp
                row_hits.append({"boundary":boundary,"subject":s.get("subject"),"id":s.get("rpt_entry_id"),"objective_match":same_objective,"sp_match":same_sp})
                if not same_objective or not same_sp:
                    return current
                updated=dict(current)
                updated["AKTIVITI UTAMA"]=activity
                allowed={"AKTIVITI UTAMA"}
                if corrected_objective:
                    updated[objective_key]=jawi_display_digits(corrected_objective)
                    allowed.add(objective_key)
                assert {k:v for k,v in updated.items() if k not in allowed}=={k:v for k,v in current.items() if k not in allowed}
                return updated
            def qa_rows(s,t):
                return replace_activity(s,original(s,t),"rows")
            runtime._rph_rows=qa_rows
            if callable(original_document):
                def qa_document(s,current):
                    return replace_activity(s,original_document(s,current),"document_rows")
                runtime._rph_document_rows=qa_document
            # The actual app native _create_rph_word resolves _rph_rows and
            # _rph_document_rows from its defining global namespace. Verify
            # this even if a runtime shim has wrapped/re-exported the engine.
            renderer=getattr(runtime,"_create_rph_word",None)
            native_globals=getattr(renderer,"__globals__",None)
            prior_globals={}
            if isinstance(native_globals,dict) and native_globals is not vars(runtime):
                for name,fn in (("_rph_rows",qa_rows),("_rph_document_rows",getattr(runtime,"_rph_document_rows",None))):
                    if name in native_globals and callable(fn):
                        prior_globals[name]=native_globals[name]
                        native_globals[name]=fn
            tag=f"PI_T{item['year']}_PDP{item['pdp']:03d}"
            unique="pi_editorial_"+uuid.uuid4().hex[:16]
            try:
                word=Path(runtime.create_word_file(state,native,unique))
                pdf=Path(runtime.create_pdf_file(state,native,unique+"p"))
                document=Document(str(word))
                changed_cells=compare_word_layout(baseline_document,document,[title for title,body in item["activities"]],item["objective"],corrected_objective)
                whole="\n".join(c.text for t in document.tables for r in t.rows for c in r.cells)
                if corrected_objective:
                    assert normalized(corrected_objective) in normalized(whole),(tag,"corrected objective absent")
                    assert normalized(item["objective"]) not in normalized(whole),(tag,"old objective still printed")
                print("PI_QA_RENDER_HOOKS",tag,row_hits,flush=True)
                print("PI_QA_WORD_ACTUAL",tag,repr(whole[:5000]),flush=True)
                for title,body in item["activities"]:
                    assert normalized(title) in normalized(whole), (tag,"missing title",title)
                    assert normalized(body) in normalized(whole), (tag,"missing activity",body)
                with fitz.open(str(pdf)) as rendered:
                    assert len(rendered)==1,(tag,"native PDF page count",len(rendered))
                    assert abs(rendered[0].rect.width-595.3)<2 and abs(rendered[0].rect.height-841.9)<2
                    rendered[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(str(root/(tag+".png")))
                shutil.copy2(word,root/(tag+".docx"))
                shutil.copy2(pdf,root/(tag+".pdf"))
                word.unlink(missing_ok=True)
                pdf.unlink(missing_ok=True)
                reports.append({"id":item["id"],"year":item["year"],"pdp":item["pdp"],"status":"NATIVE_OUTPUT_QA_ONLY","original_chars":len(rows["AKTIVITI UTAMA"]),"candidate_chars":len(activity),"native_pdf_pages":1,"changed_word_cells":changed_cells,"non_activity_word_layout_identical":not bool(corrected_objective),"non_target_word_layout_identical":True,"objective_corrected":bool(corrected_objective),"preview_png":tag+".png"})
                print("PI_EDITORIAL_RENDER",json.dumps(reports[-1]),flush=True)
            finally:
                runtime._rph_rows=original
                if callable(original_document): runtime._rph_document_rows=original_document
                if isinstance(native_globals,dict): native_globals.update(prior_globals)
        (root/"report.json").write_text(json.dumps(reports,indent=2),encoding="utf8")
        assert len(reports)==len(records)
    finally:
        runtime._rph_rows=original
        if callable(original_document): runtime._rph_document_rows=original_document
        tmp.cleanup()

if __name__=="__main__":
    main()
