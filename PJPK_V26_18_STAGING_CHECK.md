# PJPK v26.18 — staging verification (no production deployment)

Local isolated test, from repository root:

```bash
python rebuild_pjpk_candidate.py
python test_pjpk_v26_18_staging.py
```

The candidate database is separate from the existing CikguLaju curriculum database. The rebuild script preserves an existing candidate DB and checks SQLite integrity before creating it. Never rename candidate DB to the existing production DB filename.

The app bridge is OFF by default. An internal test of the bridge requires these environment variables set in a disposable staging environment **before app startup**:

```
CIKGULAJU_PJPK_T3_EDITORIAL_PREVIEW=1
CIKGULAJU_PJPK_T3_CANDIDATE_DB=/absolute/path/to/pjpk_candidate.db
```

This does not add a Telegram user-facing PJPK menu or approve production RPH. It also does not replace the application's existing split-DB bootstrap. Do not enable this on production Render, merge into main, or deploy without explicit approval. PK RPT ordering, textbook page boundaries and teacher editorial approval remain pending.

Offline ZIP validation (2026-10-12): rebuild succeeded, PRAGMA integrity_check=ok, Python AST parse succeeded for app.py/adapter/rebuild, 33 PJ + 10 PK preview calls passed, all 43 production attempts blocked. This is NOT a live Render runtime result.
