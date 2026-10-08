"""Optional PJPK RPH integration for app.py (staging only).

Install by calling install_pjpk_bridge(globals()) at the END of app.py,
after the final _local_rph_text definition. No DB write or schema migration.
"""
from pjpk_rpt_bridge_v2659 import enrich_pjpk_rph

def install_pjpk_bridge(namespace):
    original = namespace.get("_local_rph_text")
    db_factory = namespace.get("_db")
    if not callable(original) or not callable(db_factory):
        return False
    if getattr(original, "_pjpk_rpt_bridge_installed", False):
        return True

    def _pjpk_rph_with_verified_rpt(selection, *args, **kwargs):
        if not isinstance(selection, dict):
            return original(selection, *args, **kwargs)
        # Preserve all original behaviour for subjects other than PJ and PK.
        if (selection.get("subject") or selection.get("subject_name")) not in (
            "Pendidikan Jasmani", "Pendidikan Kesihatan"
        ):
            return original(selection, *args, **kwargs)
        enriched = enrich_pjpk_rph(selection, db_factory)
        return original(enriched, *args, **kwargs)

    _pjpk_rph_with_verified_rpt._pjpk_rpt_bridge_installed = True
    namespace["_local_rph_text"] = _pjpk_rph_with_verified_rpt
    return True
