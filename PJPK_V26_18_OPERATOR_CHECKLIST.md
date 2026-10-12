# PJPK v26.18 — operator checklist (staging only)

Verified offline against the uploaded ZIP on 2026-10-12: SQLite integrity OK; 33 PJ + 10 PK preview options; all 43 previews generated; all 43 production attempts blocked. Extracted bridge nodes were executed in isolation: OFF disabled, ON with missing candidate DB disabled, ON with candidate DB enabled, production request rejected. This does **not** prove full Flask/Telegram runtime on Render.

## Operator action (only when ready to test a separate staging environment)
1. Stay on branch `staging/pjpk-v26-18-review`. Do not merge into `main`.
2. In a disposable local/staging checkout run `python rebuild_pjpk_candidate.py` then `python test_pjpk_v26_18_staging.py` and `python test_pjpk_v26_18_bridge_gate.py`.
3. Keep `CIKGULAJU_PJPK_T3_EDITORIAL_PREVIEW` unset or `0` in production. Do not point `CIKGULAJU_PJPK_T3_CANDIDATE_DB` at the production curriculum DB.
4. No production deployment or database replacement is authorized. The bridge is internal-only and does not create a user-facing Telegram callback/menu.

Release blockers: independent full-app runtime verification, teacher editorial review, PK RPT ordering verification, textbook page boundary review. All existing DB data must remain intact.
