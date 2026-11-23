"""Explicit, bounded one-time private RPT Word Storage migration on Render startup.

OFF unless TWO operator-set environment flags are YES; never invoked from any
Web endpoint, user request, or CI. Only five pre-verified KSSR BM documents.
Remove flags once verification succeeds.
"""
from __future__ import annotations
import os

def stage_only_when_approved() -> bool:
    if (os.environ.get("CIKGULAJU_PRIVATE_WORD_MIGRATION_OK") != "YES"
            or os.environ.get("CIKGULAJU_PRIVATE_WORD_MIGRATION_ON_STARTUP") != "YES"):
        return False
    from tools.migrate_rpt_bm_kssr_word_private import migrate
    years = migrate(upload=True)
    if years != [2,3,4,5,6]:
        raise RuntimeError("Unexpected private Word migration result")
    # No secrets, object URLs or teacher identities in logs.
    print("CIKGULAJU_BM_KSSR_PRIVATE_WORD_VERIFIED_2_TO_6", flush=True)
    return True
