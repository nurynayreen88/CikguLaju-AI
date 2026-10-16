# PJPK v26.18 — operator checklist (staging only)

## Current status
The all-year private draft menu is wired into the existing bot on this staging branch. It is hidden from ordinary users and is not a production RPH feature.

## Private tester gate
- Only in a disposable staging environment, set `PJPK_SAME_BOT_TESTER_IDS` to the Telegram chat IDs explicitly approved for private testing.
- Leave the variable unset in production. Do not enable the separate T3 editorial bridge in production.
- The private hook validates the candidate DB and required tables. If the candidate DB is missing, it can rebuild from the committed `pjpk_candidate.db.part1` and `pjpk_candidate.db.part2` files after tester authorization. It never overwrites an existing candidate DB or the master curriculum DB.
- The menu uses a read-only, connection-local TEMP VIEW if the cached all-year menu table is absent. No master/candidate schema mutation is required for this view.
- A generated PDF is explicitly labelled as an unapproved draft; it is not the official CikguLaju RPH template.

## Automated checks
- Python syntax check passed.
- Candidate SQLite integrity and the 43 T3 editorial gates passed.
- All-year menu: 161 records total; 13 textbook-unit anchors and 1 source-conflict record are blocked; 10 duplicate records are quarantined.
- 137 remaining draft PDFs passed CI; 24 blocked/quarantined records are rejected.
- Non-PJPK callbacks and ordinary subject menu remain on the original handlers. Telegram delivery false acknowledgements are rejected.

## Release blockers
- DSKP wording/code reconciliation and exact textbook crosswalk are not fully verified.
- Teacher editorial approval and RPT sequence/page-boundary review are still required.
- No full live Telegram/Render runtime test has been performed.
- Do not merge to `main`, replace any master DB, or deploy until explicitly approved.
