# English Primary Year 2–6 — 800-Lesson technical QA handover (4 November 2026)

## Scope and result

All **800** source-linked native Word/PDF RPH data rows were audited in an isolated GitHub Actions runner, **160 Lesson per Year**, with **zero remaining technical mapping blockers**. This is **not FINAL READY** teacher/pedagogical approval, not full independent Student's Book/Workbook/audio matching, and not real-user Telegram native PDF delivery proof.

| Year | Fixed-SOW source/CS/LS mapping passed | Teacher-choice DRAF | Audio-conflict DRAF | Total |
|---|---:|---:|---:|---:|
| 2 | 160 | 0 | 0 | 160 |
| 3 | 160 | 0 | 0 | 160 |
| 4 | 149 | 10 | 1 | 160 |
| 5 | 151 | 9 | 0 | 160 |
| 6 | 146 | 14 | 0 | 160 |
| **Total** | **766** | **33** | **1** | **800** |

**Status rules**

- `SOURCE_MAPPING_PASS_FINAL_QA_PENDING` (766): SOW lesson ID, Main/Complementary code (where applicable), substantive lesson-specific Word/PDF field replacements and preservation of teacher data passed offline. Does not authorise FINAL READY.
- `TEACHER_CHOICE_DRAFT_DSKP_SELECTION_PENDING` (33): SOW does not fix CS/LS. Teacher must choose a valid DSKP standard. RPH is a CikguLaju teacher-choice suggestion, **not an official prescribed SOW project**.
- `AUDIO_SOURCE_CONFLICT_DRAFT` (1): Year4 Lesson30 — printed TB says CD1 Track29 but SOW refers CD2 Track29. Actual audio content still needs independent comparison; no confirmed equivalence.
- `TECHNICAL_BLOCKER` (0): No row-level source binding, teacher data or document field regression detected by this audit.

## Changes made in this audit

1. **Year4 142 lesson objectives:** Most reviewed fixed-standard standalone sources carried no explicit learning-objective header, so native Word/PDF could inherit an unrelated generic legacy objective. A guarded runtime-only derivation now chooses a lesson-specific pupil action from the source's actual Lesson/PBD phase; labelled **Suggested from source pupil task**. Seven earlier explicit objectives are retained. Original RPH files and their prior QA notices were not rewritten.
2. **Year6 146 fixed-standard lessons:** Titles now come from the validated official SOW topic/focus, rather than a legacy generic title. Existing source code pairs and SOW task-overlay codes must agree. Teacher-entered `REFLEKSI` is preserved.
3. **Year6 14 teacher-choice lessons:** All four Word/PDF Main/Complementary CS/LS cells display an explicit teacher-choice placeholder. Title is labelled `CADANGAN CIKGULAJU (DRAF)`; no official code is invented. Source PBD includes distinct teacher and pupils' actions plus the existing lesson-specific assessment evidence.
4. **Word A4 regression:** The existing AST-locked native Word table was rendered with local LibreOffice. Year4 fixed **148/149** were already 1 page A4; only **Lesson002** required a text-preserving scoped 8pt compactor, and then **149/149** passed. For Year6 teacher-choice, 8pt passed 13/14; **Lesson016** required a scoped 7.5pt variant, and then **14/14** passed. Other Word files remain at their previous settings.
5. **End-to-end safety:** Year1, other subjects, user records, billing/credits, RPT, database v26.00 content, teacher menu, bot callbacks, and existing final `release_approvals_2027.json` were not changed.

## Evidence and limitations

- `tools/audit_english_2_6_release_status_20261104.py` generates the **full 800-Lesson JSON ledger** with per-lesson status, source metadata, and explicit evidence gaps; see the `english-2-6-800-lesson-release-status` CI artifact.
- `tools/verify_english_y4_y6_a4_20261104.py` tests Word text preservation and 1-page A4 and archives source-specific per-Lesson layout findings.
- Word-to-PDF via LibreOffice is a **layout QA proxy**, not actual production native-PDF generation or Telegram teacher delivery.
- Do not claim all 800 Lesson are FINAL READY merely because this audit is green. Every Lesson still needs source/content/audio review when applicable and independent final teacher approval, especially teacher-choice standards and the Year4 L30 audio discrepancy.

## Safe next release gates

1. Independently inspect cited page/activities against original Student's Book, Teacher's Book and Workbook for each outstanding Lesson; record evidence by Lesson and source checksum.
2. Verify audio contents and actual bot track routing for audio-using lessons; resolve Year4 L30 audio discrepancy with recorded proof.
3. Run actual Word **and native PDF** generation/delivery under a controlled teacher Telegram test account; capture A4/screenshots and preserve credits.
4. Approve exact Lesson source checksums manually; only then set that Lesson to FINAL READY. Never bulk-promote unverified drafts.
