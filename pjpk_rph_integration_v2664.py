"""Optional PJPK RPH integration for app.py (staging only).

Uses only uniquely verified RPT/SK/SP records. If verification fails, preserves
the existing generator as a fallback. Does not mutate the curriculum database.
"""
from pjpk_rpt_bridge_v2659 import enrich_pjpk_rph
from pjpk_rph_composer_v2669 import render_verified_pjpk_text

def install_pjpk_bridge(namespace):
    original = namespace.get("_local_rph_text")
    db_factory = namespace.get("_db")
    if not callable(original) or not callable(db_factory):
        return False
    if getattr(original, "_pjpk_rph_bridge_v2664", False):
        return True

    def _pjpk_rph_with_verified_rpt(selection, *args, **kwargs):
        if not isinstance(selection, dict):
            return original(selection, *args, **kwargs)
        subject = (selection.get("subject") or selection.get("subject_name") or "").strip()
        # Keep every non-PJPK subject on its exact existing path.
        if subject not in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
            return original(selection, *args, **kwargs)
        # Only replace the legacy RPH when exact verified RPT + one SK/SP
        # can be resolved and four complete activity phases are produced.
        try:
            composed = render_verified_pjpk_text(selection, db_factory)
            if composed:
                return composed
        except Exception:
            # Fail closed to the existing generator; never fabricate a mapping.
            pass
        return original(selection, *args, **kwargs)

    _pjpk_rph_with_verified_rpt._pjpk_rph_bridge_v2664 = True
    namespace["_local_rph_text"] = _pjpk_rph_with_verified_rpt
    return True
