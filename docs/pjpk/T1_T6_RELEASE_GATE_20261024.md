# PJPK T1–T6 release gate (24 October 2026)

This is a non-destructive staging checkpoint, not an assertion that the curriculum is complete.

Source-gate inventory: 161 records: Year 1 44, Year 2 53, Year 3 23, Year 4 11, Year 5 19, Year 6 11. Of these, 13 Year 3 entries are textbook references, not PdP identities. All 161 had production_ready=0 at the audited checkpoint.

Release requirements per PdP: directly verify authoritative DSKP SK/SP code and exact text, RPT lesson/slot, textbook linkage (or explicitly mark unavailable), substantive subject-specific one-page RPH, engine-generation smoke test, and preserve all existing DB/data. Do not promote reference-only entries into PdP identities. Preserve any pre-existing approved functionality. Backup/version database before any migration. Do not deploy this checkpoint as a completed PJPK release.

Prioritized next work: compare current repository DB and staging schemas with 161-row source gate; resolve conflicting evidence; only migrate approved rows additively; run generation tests for all six years and both PJ and PK; then deploy and verify Render runtime.
