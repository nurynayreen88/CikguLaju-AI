"""Off-by-default same-bot PJPK draft preview; production RPH remains blocked."""
import csv
import os
import sqlite3
import tempfile
from pathlib import Path
from html import escape as html_escape

from pjpk_private_menu import list_menu_rows, entry_status

def install(namespace):
    root = Path(namespace.get("__file__", __file__)).resolve().parent
    quarantine_path = root / "COLLISION_QUARANTINE_10.csv"
    with quarantine_path.open(encoding="utf-8-sig", newline="") as source:
        quarantine = {int(row["entry_id"]) for row in csv.DictReader(source)}
    if len(quarantine) != 10:
        raise RuntimeError("Fail closed: PJPK collision quarantine must contain exactly 10 IDs")

    original_subjects = namespace.get("subjects")
    original_callback = namespace.get("callback")
    send = namespace.get("send")
    send_document = namespace.get("send_document")
    delivery_ok = namespace.get("_telegram_delivery_ok_v25279")
    if not all(callable(x) for x in (original_subjects, original_callback, send, send_document, delivery_ok)):
        return False

    tester_ids = {
        int(value.strip())
        for value in os.getenv("PJPK_SAME_BOT_TESTER_IDS", "").split(",")
        if value.strip().isdigit()
    }
    db_path = root / "pjpk_candidate.db"
    part_paths = (root / "pjpk_candidate.db.part1", root / "pjpk_candidate.db.part2")
    required_tables = {
        "rpt_entries", "rpt_entry_standards", "pjpk_v47_generator_gate",
        "pjpk_v53_entry_classification", "pjpk_v59_source_kind_guard",
        "pjpk_dskp_provenance", "pjpk_v52_source_backed_repair",
        "pjpk_v55_source_correction", "pjpk_v62_slot_preview_scope",
        "pjpk_v64_t3_specific_activity", "pjpk_v67_pk_t5_verified_source_staging",
        "pjpk_v70_pk_t5_specific_activity", "pjpk_v57_specific_activity",
        "pjpk_v58_sp_activity_drafts", "pjpk_v49_verified_additive_link",
        "pjpk_v40_page_sp_crosswalk",
    }

    def ensure_candidate_db():
        # Existing candidate files are never overwritten. A missing file may be
        # reconstructed from the committed parts into a temporary file, validated,
        # and linked atomically into place.
        if not db_path.is_file():
            if not all(path.is_file() for path in part_paths):
                return False
            fd, temp_name = tempfile.mkstemp(prefix="pjpk-candidate-", suffix=".db", dir=str(root))
            os.close(fd)
            temp_path = Path(temp_name)
            try:
                with temp_path.open("wb") as output:
                    for part in part_paths:
                        with part.open("rb") as source:
                            while True:
                                block = source.read(1024 * 1024)
                                if not block:
                                    break
                                output.write(block)
                if not validate_candidate(temp_path):
                    return False
                try:
                    os.link(str(temp_path), str(db_path))
                except FileExistsError:
                    pass
            finally:
                try:
                    temp_path.unlink()
                except FileNotFoundError:
                    pass
        return validate_candidate(db_path)

    def validate_candidate(path):
        try:
            uri = path.resolve().as_uri() + "?mode=ro"
            with sqlite3.connect(uri, uri=True) as con:
                if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    return False
                tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if not required_tables.issubset(tables):
                    return False
                count = con.execute("SELECT COUNT(*) FROM pjpk_v47_generator_gate").fetchone()[0]
                if count != 161:
                    return False
            return True
        except (OSError, sqlite3.Error):
            return False

    def allowed(chat_id):
        try:
            return bool(tester_ids) and int(chat_id) in tester_ids and ensure_candidate_db()
        except (ValueError, TypeError):
            return False

    def rows_for(year, component):
        if not ensure_candidate_db():
            return []
        return list_menu_rows(db_path, year=int(year), component=component)

    def private_menu(chat_id, year, component):
        rows = rows_for(year, component)
        buttons = [
            [{"text": f'{row["entry_id"]} — {str(row["topic"] or "Tanpa tajuk")[:35]}',
              "callback_data": "pjpkprivate_pdf_" + str(row["entry_id"])}]
            for row in rows
            if row["entry_status"] == "REVIEW_ONLY" and int(row["entry_id"]) not in quarantine
        ]
        buttons.append([{"text": "⬅️ PJ/PK Tahun " + str(year), "callback_data": "pjpkprivate_year_" + str(year)}])
        return send(
            chat_id,
            "<b>PRATONTON " + html_escape(component) + " TAHUN " + str(year) +
            "</b>\nDRAF BELUM DILULUSKAN — bukan RPH produksi.",
            buttons
        )

    def wrapped_subjects(chat_id, label):
        result = original_subjects(chat_id, label)
        if allowed(chat_id):
            import re
            match = re.fullmatch(r"Tahun ([1-6])", str(label or ""))
            if match:
                year = match.group(1)
                send(chat_id, "PJPK — PRATONTON PENGUJI SAHAJA (menu biasa kekal)", [
                    [{"text": "Pendidikan Jasmani (DRAF)", "callback_data": "pjpkprivate_subject_" + year + "_PJ"}],
                    [{"text": "Pendidikan Kesihatan (DRAF)", "callback_data": "pjpkprivate_subject_" + year + "_PK"}],
                ])
        return result

    def wrapped_callback(chat_id, data):
        data = str(data or "")
        if not data.startswith("pjpkprivate_"):
            return original_callback(chat_id, data)
        if not allowed(chat_id):
            return send(chat_id, "PJPK belum dibuka untuk pengguna.")
        import re
        match = re.fullmatch(r"pjpkprivate_year_([1-6])", data)
        if match:
            year = match.group(1)
            return send(chat_id, "PJPK Tahun " + year + " — DRAF belum diluluskan", [
                [{"text": "Pendidikan Jasmani", "callback_data": "pjpkprivate_subject_" + year + "_PJ"}],
                [{"text": "Pendidikan Kesihatan", "callback_data": "pjpkprivate_subject_" + year + "_PK"}],
            ])
        match = re.fullmatch(r"pjpkprivate_subject_([1-6])_(PJ|PK)", data)
        if match:
            return private_menu(chat_id, int(match.group(1)), match.group(2))
        match = re.fullmatch(r"pjpkprivate_pdf_([0-9]{1,9})", data)
        if not match:
            return send(chat_id, "Pilihan PJPK tidak sah.")
        entry_id = int(match.group(1))
        status = entry_status(db_path, entry_id) if ensure_candidate_db() else None
        if entry_id in quarantine or status != "REVIEW_ONLY":
            return send(chat_id, "Rekod ini disekat; PDF tidak dijana.")
        from preview_server import pdf
        with tempfile.TemporaryDirectory(prefix="pjpk_draft_") as temp_dir:
            pdf_path = Path(temp_dir) / ("PJPK_DRAF_" + str(entry_id) + ".pdf")
            pdf_path.write_bytes(pdf(entry_id))
            result = send_document(
                chat_id, str(pdf_path),
                "DRAF PJPK — BELUM DILULUSKAN; bukan RPH produksi."
            )
            if not delivery_ok(result):
                raise RuntimeError("Telegram did not confirm PJPK draft delivery")
            return result

    wrapped_subjects._pjpk_private_v4 = True
    wrapped_callback._pjpk_private_v4 = True
    namespace["subjects"] = wrapped_subjects
    namespace["callback"] = wrapped_callback
    return True
