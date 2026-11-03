# English Year 5 — Telegram production release gate (03 November 2026)

## Staging results
- Source branch: `english-year5-rph-lesson1`, original 160 draft Markdown files imported without destructive replacement.
- Integrated branch: `feat/english-y5-standalone-telegram-20261103`; PR #158.
- Official Year 5 SK SOW lesson table: **160 lessons**, **151 with fixed Main + Complementary LS**, **nine teacher-selected**: 16, 34, 52, 70, 88, 106, 124, 142, 160.
- Lesson 141 official source discrepancy: lesson table complementary **4.2.4**; Appendix 1 / existing RPH **4.2.2**. Remains fail-closed, not READY.
- 15 missing lesson objectives supplied as bounded and task-specific in the staging sources only.
- After format repairs, **150/150 remaining fixed-code lessons parse correctly and match both official lesson-table LS**. Offline row-adapter smoke checks cover 150 plans; no database or user accounts are used.
- PR CI regression: Year 4 runtime, Year 6 runtime, English RPT 2027, English RPH internal notes and Year 5 adapter tests all passed on commit `e6180c7`.

## What is and is not released
- The Telegram bridge is deliberately **disabled by default**: it requires `CIKGULAJU_Y5_DRAFT_RPH_ENABLED=1` for a controlled, explicitly authorised test.
- Existing generator, quota controls, Telegram callbacks, Year 4/6 bridges and user/database state remain authoritative; if a source is missing, not fully parsed, or standards mismatch, the bridge preserves the original rows.
- The nine teacher-selected lessons and disputed Lesson 141 do **not** override legacy RPH until reviewed/approved.
- These source RPH remain **DRAF** and should not be marketed as READY to teachers. A parser pass is not equivalent to textbook exercise, Workbook page, audio or classroom validity.
- Remaining READY requirements: complete book-page/task and audio playback QA; verified RPT 2027 scheduling; actual Telegram Word/PDF one-page A4 downloads; individual content/teacher approval and an explicit per-lesson READY ledger.

## Rollout
1. Run isolated/pilot Word+PDF rendering and approve one-page A4 before enabling live.
2. Verify specific lessons from each SOW unit, literature exception and teacher-selected group.
3. Resolve Lesson 141 against curriculum authority or record a justified manual decision.
4. Only then enable production flag, carry out a real Telegram test and mark approved lessons READY. Do not silently approve all 160.
