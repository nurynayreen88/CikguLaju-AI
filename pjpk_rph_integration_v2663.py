"""Opt-in PJPK integration for CikguLaju, v26.63.

Usage at the END of app.py, after the final _local_rph_text definition:
    from pjpk_rph_integration_v2663 import install_pjpk_rph_bridge
    install_pjpk_rph_bridge(globals())

No database writes, no automatic install, and no changes to other subjects.
"""
from pjpk_rpt_bridge_v2659 import enrich_pjpk_rph

def install_pjpk_rph_bridge(namespace):
    previous = namespace.get("_local_rph_text")
    connect = namespace.get("_db")
    if not callable(previous) or not callable(connect):
        return False
    if getattr(previous, "_pjpk_rpt_bridge_v2663", False):
        return True

    def _pjpk_enriched_local_rph_text(selection):
        if not isinstance(selection, dict):
            return previous(selection)
        subject = selection.get("subject") or selection.get("subject_name")
        if subject not in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
            return previous(selection)
        enriched = enrich_pjpk_rph(selection, connect)
        return previous(enriched)

    _pjpk_enriched_local_rph_text._pjpk_rpt_bridge_v2663 = True
    namespace["_local_rph_text"] = _pjpk_enriched_local_rph_text
    return True
