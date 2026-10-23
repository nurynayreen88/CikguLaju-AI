# PJPK Tahun 1–6: batch audit v26.80

This is an audit aid, **not** a curriculum release or a database migration.

Run from the repository root after reconstructing the existing isolated candidate database using the existing v26.79 workflow:

```bash
python -m unittest tests/test_pjpk_12_scope_summary_v2680.py
python scripts/pjpk_source_gap_queue_v2679.py --db PATH_TO_EXISTING_CANDIDATE.db --format csv > pjpk_source_gap_queue.csv
python scripts/pjpk_12_scope_summary_v2680.py --db PATH_TO_EXISTING_CANDIDATE.db > pjpk_12_scope_summary.json
```

The summary always includes 12 year/subject scopes, even those with zero queued issues. It counts **review rows**, not unique RPT lessons. Each queue record must remain source-reviewed against exact-year and exact-subject DSKP/RPT before any production promotion. A missing SK link is not permission to infer SK. The scripts do not update source DB bytes, app.py, DB_PATH, production gates or Render.

Previously reported v26.79 baseline: 170 SP source reviews plus 128 missing SK links (298 review rows). Re-run against the current candidate DB before claiming these counts remain current. Release readiness additionally requires the existing verified-only adapter and end-to-end RPH/PDF tests; this summary alone cannot certify readiness.
