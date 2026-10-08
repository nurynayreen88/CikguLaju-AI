"""PJPK v26.66: safe opt-in adapter for verified RPH activities.

This module never edits the database and never patches unrelated subjects.
The existing RPH renderer may use selection['_pjpk_activity_phases_v2666']
when rendering its activity section. Merely importing this file has no effect.
"""
from pjpk_rpt_bridge_v2659 import enrich_pjpk_rph
from pjpk_activity_planner_v2665 import build_pjpk_activities

SUBJECTS = frozenset(("Pendidikan Jasmani", "Pendidikan Kesihatan"))

def prepare_pjpk_rph(selection, connect):
    """Enrich a copy using verified standards; never replace original on failure."""
    if not isinstance(selection, dict):
        return selection
    result = dict(selection)
    if (result.get("subject") or result.get("subject_name")) not in SUBJECTS:
        return result
    try:
        verified = enrich_pjpk_rph(result, connect)
        if not isinstance(verified, dict):
            return result
        if not verified.get("_pjpk_standards_complete_v2659"):
            return result
        for key in ("sk_code", "sp_code", "sk_text", "sp_text"):
            if result.get(key) and str(result[key]).strip() != str(verified.get(key) or "").strip():
                return result
        phases = build_pjpk_activities(verified)
        if not phases:
            return result
        verified["_pjpk_activity_phases_v2666"] = tuple(phases)
        verified["_pjpk_activity_verified_v2666"] = True
        return verified
    except (TypeError, ValueError, KeyError, AttributeError):
        return result

def install_pjpk_activity_adapter(namespace):
    """Explicit opt-in wrapper around existing _local_rph_text.

    The original generator receives verified phases in the selection dict;
    it must explicitly support that key before activities appear in PDF.
    """
    original = namespace.get("_local_rph_text")
    connect = namespace.get("_db")
    if not callable(original) or not callable(connect):
        return False
    if getattr(original, "_pjpk_activity_adapter_v2666", False):
        return True
    def wrapped(selection, *args, **kwargs):
        return original(prepare_pjpk_rph(selection, connect), *args, **kwargs)
    wrapped._pjpk_activity_adapter_v2666 = True
    namespace["_local_rph_text"] = wrapped
    return True
