"""PJPK RPT bridge v26.59 (opt-in). Does not mutate the curriculum database.
Only attaches uniquely identified, verified RPT and SK/SP text. Integration into
app.py must be reviewed separately; importing this module alone changes nothing.
"""
import re
import sqlite3

def enrich_pjpk_rph(selection, connect):
    if not isinstance(selection, dict):
        return selection
    result = dict(selection)
    subject = result.get("subject") or result.get("subject_name")
    if subject not in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
        return result
    year = str(result.get("year_label") or result.get("year") or "").strip()
    if re.fullmatch(r"[1-6]", year):
        year = "Tahun " + year
    if not re.fullmatch(r"Tahun [1-6]", year):
        return result
    # lesson_no is a user-facing lesson index, not necessarily the DB RPT sequence.
    seq = result.get("rpt_sequence_no") or result.get("sequence_no")
    topic = str(result.get("topic") or result.get("topic_title") or "").strip()
    if not (str(seq).isdigit() or topic):
        return result
    con = None
    try:
        con = connect()
        if con is None:
            return result
        entry_columns = {x[1] for x in con.execute("PRAGMA table_info(rpt_entries)").fetchall()}
        standard_columns = {x[1] for x in con.execute("PRAGMA table_info(rpt_entry_standards)").fetchall()}
        required_entries = {"id", "year_label", "subject", "sequence_no", "topic", "verified", "content_verified"}
        required_standards = {"rpt_entry_id", "standard_type", "standard_code", "standard_text", "verified"}
        if not required_entries.issubset(entry_columns) or not required_standards.issubset(standard_columns):
            return result
        entry_order = "id"
        standard_order = ",".join(c for c in ("sequence_no", "id") if c in standard_columns) or "standard_code"
        if str(seq).isdigit():
            rows = con.execute(
                "SELECT * FROM rpt_entries WHERE year_label=? AND subject=? AND sequence_no=? AND verified=1 AND content_verified=1 ORDER BY " + entry_order + " LIMIT 2",
                (year, subject, int(seq))).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM rpt_entries WHERE year_label=? AND subject=? AND lower(trim(topic))=lower(?) AND verified=1 AND content_verified=1 ORDER BY id LIMIT 2",
                (year, subject, topic)).fetchall()
        if len(rows) == 0 and topic:
            rows = con.execute(
                "SELECT * FROM rpt_entries WHERE year_label=? AND subject=? AND lower(trim(topic))=lower(?) AND verified=1 AND content_verified=1 ORDER BY id LIMIT 2",
                (year, subject, topic)).fetchall()
        if len(rows) != 1:
            return result
        if topic and str(seq).isdigit():
            check_cols = [d[0] for d in con.execute("SELECT * FROM rpt_entries LIMIT 0").description]
            check_row = dict(zip(check_cols, rows[0]))
            if str(check_row.get("topic") or "").strip().casefold() != topic.casefold():
                # Sequence may refer to a different unit; never silently reuse it.
                rows = con.execute(
                    "SELECT * FROM rpt_entries WHERE year_label=? AND subject=? AND lower(trim(topic))=lower(?) AND verified=1 AND content_verified=1 ORDER BY id LIMIT 2",
                    (year, subject, topic)).fetchall()
                if len(rows) != 1:
                    return result
        cols = [d[0] for d in con.execute("SELECT * FROM rpt_entries LIMIT 0").description]
        r = dict(zip(cols, rows[0]))
        standards = con.execute(
            "SELECT standard_type,standard_code,standard_text FROM rpt_entry_standards WHERE rpt_entry_id=? AND verified=1 ORDER BY " + standard_order,
            (r["id"],)).fetchall()
        sk = [x for x in standards if x[0] == "SK" and str(x[2] or "").strip() and str(x[1] or "").strip()]
        sp = [x for x in standards if x[0] == "SP" and str(x[2] or "").strip() and str(x[1] or "").strip()]
        if not result.get("sk_code") and len(sk) == 1:
            result["sk_code"], result["sk_text"] = sk[0][1], sk[0][2]
        if not result.get("sp_code") and len(sp) == 1:
            result["sp_code"], result["sp_text"] = sp[0][1], sp[0][2]
        for field in ("topic", "subtopic", "skill_focus", "unit_title"):
            if field in r and not result.get(field) and r.get(field):
                result[field] = r[field]
        result["_pjpk_rpt_source_id_v2659"] = r["id"]
        result["_pjpk_verified_sp_details_v2662"] = [{"code": str(x[1]), "text": str(x[2])} for x in sp]
        result["_pjpk_verified_sk_details_v2662"] = [{"code": str(x[1]), "text": str(x[2])} for x in sk]
        result["_pjpk_verified_sp_codes_v2661"] = [str(x[1]) for x in sp]
        result["_pjpk_verified_sk_codes_v2661"] = [str(x[1]) for x in sk]
        result["_pjpk_multiple_sp_v2661"] = len(sp) > 1
        result["_pjpk_standards_complete_v2659"] = bool(result.get("sk_code") and result.get("sp_code") and result.get("sk_text") and result.get("sp_text"))
        return result
    except (sqlite3.Error, ValueError, TypeError, KeyError, AttributeError, IndexError):
        return result
    finally:
        if con is not None:
            try:
                con.close()
            except sqlite3.Error:
                pass
