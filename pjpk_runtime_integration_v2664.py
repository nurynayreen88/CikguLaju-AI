"""Opt-in PJPK integration for CikguLaju app.py; safe fallback for legacy DBs.

Install by importing install_pjpk_bridge(globals()) at the END of app.py.
No database writes. Never fabricates SK/SP. Only changes RPH when both
verified SK and SP code/text are available.
"""
import sqlite3

def install_pjpk_bridge(namespace):
    original = namespace.get("_local_rph_text")
    db_path = namespace.get("DB_PATH")
    if not callable(original) or not db_path:
        return False
    try:
        from pjpk_rpt_bridge_v2659 import enrich_pjpk_rph
    except ImportError:
        return False

    def _pjpk_verified_rph(selection, *args, **kwargs):
        if not isinstance(selection, dict):
            return original(selection, *args, **kwargs)
        subject = selection.get("subject") or selection.get("subject_name")
        if subject not in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
            return original(selection, *args, **kwargs)

        def _connect():
            # Own connection, never close the application's shared connection.
            return sqlite3.connect("file:" + str(db_path) + "?mode=ro", uri=True, timeout=5)

        enriched = enrich_pjpk_rph(selection, _connect)
        if not enriched.get("_pjpk_standards_complete_v2659"):
            return original(selection, *args, **kwargs)
        # Do not overwrite existing verified/explicit standards.
        if (selection.get("sk_code") and selection.get("sk_code") != enriched.get("sk_code")) or (
            selection.get("sp_code") and selection.get("sp_code") != enriched.get("sp_code")
        ):
            return original(selection, *args, **kwargs)
        return original(enriched, *args, **kwargs)

    namespace["_local_rph_text"] = _pjpk_verified_rph
    return True
