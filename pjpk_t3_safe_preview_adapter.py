"""Standalone, read-only Year 3 PJPK editorial preview API. NOT wired to live app."""
import sqlite3
from pathlib import Path

class PreviewBlocked(ValueError): pass
def _connect(path):
    c=sqlite3.connect(Path(path).resolve().as_uri()+"?mode=ro",uri=True)
    c.row_factory=sqlite3.Row
    return c

def list_options(db_path,subject):
    if subject not in ("PJ","PK"): raise PreviewBlocked("Only PJ or PK")
    with _connect(db_path) as c:
        if subject=="PJ":
            return [{"subject":"PJ","key":str(r["week_no"]),"topic":r["topic"],"label":"Minggu RPT "+str(r["week_no"]),"status":"PREVIEW_ONLY"} for r in c.execute("select week_no,topic from pjpk_t3_pj_rph_activity_draft order by week_no")]
        return [{"subject":"PK","key":r["sk_code"],"topic":r["topic_focus"],"label":"Kelompok SK "+r["sk_code"]+" (bukan minggu RPT)","status":"PREVIEW_ONLY"} for r in c.execute("select sk_code,topic_focus from pjpk_t3_pk_activity_draft order by sk_code")]

def generate_preview(db_path,subject,key,mode="preview"):
    if mode!="preview":raise PreviewBlocked("PRODUCTION_BLOCKED: Teacher review and PK RPT not complete")
    if subject not in ("PJ","PK"):raise PreviewBlocked("Subject must be PJ or PK")
    with _connect(db_path) as c:
        if subject=="PJ":
            if not str(key).isdigit() or str(int(key))!=str(key):raise PreviewBlocked("Invalid RPT week")
            r=c.execute("select * from pjpk_t3_pj_rph_activity_draft where week_no=?",(int(key),)).fetchone()
            if not r:raise PreviewBlocked("Unknown PJ RPT slot")
            codes=[s.strip() for s in r["sp_codes"].split(",")]
            evidence_table="pjpk_t3_dskp_direct_evidence"
            title=r["topic"]
        else:
            r=c.execute("select * from pjpk_t3_pk_activity_draft where sk_code=?",(str(key),)).fetchone()
            if not r:raise PreviewBlocked("Unknown PK SK group")
            codes=[x["sp_code"] for x in c.execute("select sp_code from pjpk_t3_pk_full_dskp_evidence where sk_code=? order by sp_code",(str(key),))]
            evidence_table="pjpk_t3_pk_full_dskp_evidence"
            title=r["topic_focus"]
        if not codes or len(set(codes))!=len(codes):raise PreviewBlocked("Missing/duplicate SP")
        evidence=[]
        for sp in codes:
            x=c.execute("select sp_text from "+evidence_table+" where sp_code=?",(sp,)).fetchone()
            if not x or not x["sp_text"].strip():raise PreviewBlocked("Missing exact subject-specific DSKP text: "+sp)
            evidence.append({"code":sp,"text":x["sp_text"]})
        ed=c.execute("select * from pjpk_t3_43_editorial_gate where subject=? and scope_key=?",(subject,str(key))).fetchone()
        if not ed or ed["production_status"]!="BLOCKED" or ed["teacher_review"]!="PENDING_TEACHER_REVIEW":
            raise PreviewBlocked("Editorial gate unexpectedly changed; require fresh review")
        phases=[{"name":label,"minutes":minutes,"text":r[field]} for label,minutes,field in
                [("Set Induksi",3,"set_induksi"),("Aktiviti 1",10,"aktiviti_1"),("Aktiviti 2",10,"aktiviti_2"),("Pengukuhan/Penilaian",5,"pengukuhan_penilaian"),("Penutup",2,"penutup")]]
        if any(not p["text"] or not p["text"].strip() for p in phases):raise PreviewBlocked("Missing activity")
        book=None
        if subject=="PK":
            b=c.execute("select * from pjpk_t3_pk_textbook_bridge where sk_code=?",(str(key),)).fetchone()
            if not b or b["rpt_status"]!="PK_RPT_NOT_AVAILABLE":raise PreviewBlocked("Unexpected PK source state")
            book={"unit":b["book_unit"],"printed_page_range":b["printed_page_anchor"],"status":"REVIEW_PAGE_BOUNDARY"}
        return {"subject":subject,"key":str(key),"topic":title,"year":"Tahun 3","status":"PREVIEW_ONLY","rpt_status":"PJ_RPT_SLOT" if subject=="PJ" else "PK_RPT_NOT_AVAILABLE","sp":evidence,"phases":phases,"assessment":ed["assessment_evidence"],"safety":ed["safety_control"],"book":book,"teacher_review":"PENDING_TEACHER_REVIEW","production_allowed":False}
