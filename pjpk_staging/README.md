# PJPK private staging — NOT DEPLOYABLE YET

This branch is separate from `main`. `app.py` and the master curriculum DB have not been changed.

`private_draft_integration.py.txt` is an append-only integration candidate from the local tested package. It is deliberately stored as `.txt` to prevent accidental activation. It requires `pjpk_candidate.db`, `pjpk_rph_engine.py`, and `preview_server.py` from the separately prepared private test package. These binary/dependency files have **not** been committed here. Do not append the patch to production until the GitHub `app.py` is compared against the locally tested timetable version and the runtime function signatures are checked.

Previous local mock tests: 12 year/subject menu mappings; 147 draft PDF deliveries; 14 blocked; Telegram negative acknowledgment rejected. These are mock tests, not live Telegram/Render confirmation. Draft PDFs are not approved RPH. Public release remains disabled.

Required before release: (1) verify actual production app baseline; (2) stage the candidate DB without replacing any existing DB; (3) verify all curriculum mappings against DSKP/RPT/textbooks; (4) run actual PDF and Telegram private tester checks; (5) obtain explicit deployment approval.
