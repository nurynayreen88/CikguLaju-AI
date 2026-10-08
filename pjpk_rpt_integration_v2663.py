"""Opt-in PJPK RPT integration, v26.63.

Call install_pjpk_rpt_bridge(globals()) once AFTER all existing RPH engine
definitions in app.py. This module never modifies any SQLite database.
"""
from pjpk_rpt_bridge_v2659 import enrich_pjpk_rph

def install_pjpk_rpt_bridge(namespace):
    previous = namespace.get("_local_rph_text")
    connect = namespace.get("_db")
    if not callable(previous) or not callable(connect):
        return False
    if getattr(previous, "_pjpk_rpt_bridge_installed_v2663", False):
        return True

    def _local_rph_text_pjpk_rpt_v2663(selection, *args, **kwargs):
        enriched = enrich_pjpk_rph(selection, connect)
        return previous(enriched, *args, **kwargs)

    _local_rph_text_pjpk_rpt_v2663._pjpk_rpt_bridge_installed_v2663 = True
    namespace["_local_rph_text"] = _local_rph_text_pjpk_rpt_v2663
    return True
