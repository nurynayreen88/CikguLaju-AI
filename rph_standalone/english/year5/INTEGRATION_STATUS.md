# English Year 5 — integration staging, 3 November 2026

160/160 standalone RPH Markdown drafts copied by Git blob identity from source branch english-year5-rph-lesson1; the source files have **not** been rewritten. Official SOW lesson table supplies 151 fixed standard pairs; nine teacher-selection lessons are 16, 34, 52, 70, 88, 106, 124, 142, 160.

All RPH files remain DRAF unless independently signed off lesson-by-lesson. No production DB, credits, or teacher records may be mutated through this staging. Lesson 141 discrepancy: the official Lesson table gives complementary 4.2.4 while Appendix 1 gives 4.2.2. The existing Lesson 141 standalone source now uses the lesson-specific 4.2.4; this resolves the source-file mismatch without claiming final teacher approval. The conflicting Appendix remains documented.

This staging integration must not be called READY until source exercise, audio, one-page A4 and Telegram runtime end-to-end checks pass. Prevent replacement of existing RPH when selected lesson/standards do not match.


## Runtime handover — 4 November 2026
- The 151 fixed-standard source files parse and can be previewed through the existing offline Year 5 row adapter. Nine teacher-choice lessons remain suggestions, not official fixed SOW standard pairs.
- Telegram production intentionally does not enable `CIKGULAJU_Y5_DRAFT_RPH_ENABLED`. Every new Year 5 lesson remains **DRAF** until book/audio/A4 checks and teacher approval; no automatic bulk READY labels or quota debit.
- The source/standards QA test now runs alongside Year 2–6 document-row tests. It is not an authorisation to publish draft Year 5 downloads.

- **Additional safety gate:** `release_approvals_2027.json` starts with zero approved lessons. Even if the optional Year 5 runtime flag is switched on accidentally, production Word/PDF will not replace a lesson until its specific source SHA256 and seven teacher/source/audio/A4/delivery approvals are all present. The 151 lesson staging adapter remains available to offline audits without changing user downloads.

## Nine teacher-choice lesson proposals — 4 November 2026

The following nine SOW teacher-choice lessons now have a distinct teacher/pupil activity and PBD proposal overlay: **16, 34, 52, 70, 88, 106, 124, 142 and 160**. Each proposal totals 60 minutes and is aligned to the existing matching Lesson draft. The native Telegram Word/PDF row bridge labels every such document **CADANGAN CIKGULAJU (DRAF)** and displays **teacher must choose Year 5 DSKP standards**, never fabricated official SOW codes.

- Lessons 16, 34, 52, 70, 106, 124 and 142: Language Awareness — uses the existing SOW-referenced English Plus 1 review activity sequence.
- Lessons 88 and 160: Project-Based Learning — explicitly suggested CikguLaju projects (My Dream School Day and Eco-Holiday Brochure), not official compulsory projects.
- The existing 151 Year 5 fixed-standard lesson drafts remain behind per-lesson approval and checksum gates. No bulk READY action, no curriculum/Telegram account DB writes, and no change to the credit/entitlement system.
- **Release limitation:** This makes the nine suggestions available as labelled drafts, not independently approved teaching plans. Printed textbook page/audio checks and real-user native PDF/A4 delivery still require confirmation before final READY.
