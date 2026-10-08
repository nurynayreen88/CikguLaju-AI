"""PJPK v26.67 integration instructions and QA gates.

Do not deploy by merely importing the activity adapter:
1. Ensure app.py's final _local_rph_text accepts a selection dict.
2. At the end of app.py, explicitly call:
       from pjpk_activity_adapter_v2666 import install_pjpk_activity_adapter
       assert install_pjpk_activity_adapter(globals())
3. Inside the actual RPH activity formatter, consume
   selection.get("_pjpk_activity_phases_v2666") ONLY for PJ/PK and only when
   selection.get("_pjpk_activity_verified_v2666") is True.
4. Preserve existing bold activity headings, one-page A4 constraints and
   existing fallback for all other subjects.
5. Test at least one verified PdP per year and both PJ and PK separately.
6. Test an unverified PdP: no fabricated SK/SP, no false READY status.
7. Verify no changes to the production DB schema or row counts.
8. Validate PDF rendering (including Unicode) before merging staging.
No deployment is performed by this script.
"""
import unittest
from pjpk_activity_adapter_v2666 import prepare_pjpk_rph

def audit_selection(selection, connect):
    prepared = prepare_pjpk_rph(selection, connect)
    phases = prepared.get("_pjpk_activity_phases_v2666") if isinstance(prepared, dict) else None
    return {
        "subject": selection.get("subject") if isinstance(selection, dict) else None,
        "year": selection.get("year") if isinstance(selection, dict) else None,
        "verified": bool(prepared.get("_pjpk_activity_verified_v2666")) if isinstance(prepared, dict) else False,
        "phase_count": len(phases) if phases else 0,
        "has_sk_sp": bool(prepared.get("sk_code") and prepared.get("sp_code")) if isinstance(prepared, dict) else False,
    }

if __name__ == "__main__":
    unittest.main(module=None, exit=False)
