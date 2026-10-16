# PJPK v26.18 — staging status (private preview only)

## Implemented in this branch
- The existing bot now has a separate, tester-only PJPK draft menu for Tahun 1–6, both Pendidikan Jasmani (PJ) and Pendidikan Kesihatan (PK).
- The menu is OFF for normal users unless `PJPK_SAME_BOT_TESTER_IDS` explicitly contains their Telegram chat ID.
- If the candidate DB is missing, the private hook may reconstruct it from the committed candidate parts only after tester authorization, validates SQLite integrity and required tables, and never overwrites an existing candidate DB.
- When the candidate DB lacks the cached menu table, the helper creates a connection-local TEMP VIEW from the existing candidate tables. This is read-only and does not alter the DB file.
- The preview engine and PDF routes enforce the same gate and collision quarantine. Production mode remains blocked.

## Verified by GitHub Actions
- `py_compile` passed for app.py and PJPK modules.
- Existing v26.18 T3 isolated candidate integrity/editorial gate passed: 43 previews, 43 production attempts blocked.
- All-year candidate inventory: 161 menu entries; 147 marked REVIEW_ONLY, 13 textbook-unit anchors blocked, 1 source-conflict entry blocked.
- Ten duplicate entries are quarantined, leaving 137 draft previews. All 137 draft texts and one-page PDFs passed CI tests; all 24 blocked/quarantined records fail closed.
- Same-bot wrapper tests confirm normal subject/callback flow is preserved, private menu is hidden from non-testers, and Telegram delivery must be explicitly acknowledged.

## Not approved for production
- These are draft previews, not official production RPHs. DSKP text reconciliation and textbook crosswalk gaps remain in the data gate.
- Teacher editorial approval, RPT ordering review, exact textbook page-boundary review and live Telegram/Render runtime testing remain outstanding.
- The runtime master DB was audited read-only and contains no PJPK RPT rows under the expected labels; the private preview therefore uses the separate candidate DB, not the master DB.
- Do not set `PJPK_SAME_BOT_TESTER_IDS` on production, merge to `main`, replace the master DB, or deploy without explicit approval.
