# CikguLaju English Year 5 — 160-Lesson READY Gate Ledger

**Audit:** 3 November 2026. Branch `english-year5-rph-lesson1`. **Status: 160/160 DRAF, READY NOT CERTIFIED.** This ledger consolidates direct reads of 160 RPH files, the official Year 5 SOW and the English 2027 RPT master sheet. Screening reports were created in 12 numbered batches; their original flags reflect the *first pass* and do not disappear after targeted fixes.

## Textual scope and first-pass findings

- 160/160 files checked, 160 distinct lesson numbers; all source SOW focus labels matched their numbered RPT 2027 rows in this screen.
- 44 files received at least one *screening flag* initially; first-pass counts by flag: `PHASE` 2, `ACTORS` 22, `WRONG_BPK` 2, `WB_DUP` 7, `TIME` 2, `LS_4.2.4` 1, `GENERIC` 8.
- All files remain drafts. No automatic lesson-level READY was conferred by flag absence.

## Verified corrections following first-pass audit

- **WRONG_BPK:** Lessons 59 and 66 corrected to English Plus textbook source, based on the actual SOW and visually inspected scanned pages. Lesson 59 WB p.30 directly matches the listening unit; previously listed p.31 is grammar.
- **WB_DUP:** Lessons 86, 89, 96, 100, 109, 133, 134 had duplicate source-mapping paragraphs removed without changing lesson activities.
- **TIME:** Lessons 106, 108 had phase duration totals normalised to 60 minutes (5+40+10+5); these are provisional class timings.
- **GENERIC:** Lessons 152–159 gained differentiated, observable objectives/PBD matching the official SOW learning activities.
- **Earlier targeted visual source check:** Lesson 37: TB p.37 recommends WB p.20 for routine/frequency language, while WB p.24 is a different reading extension. Both are now distinguished.

## Official source discrepancy — do not silently overwrite

**Lesson 141:** The official Year 5 SOW's main Lesson 141 table gives complementary Writing **4.2.4**; official SOW Appendix 1 gives **4.2.2**. The branch RPH currently uses 4.2.2 while the 2027 master RPT uses 4.2.4. Both can be traced to the same official document. Status: **BLOCKED — requires an explicit approved source-precedence decision**, not an invented code or automatic overwrite.

**Lesson 159:** RPH records an additional skill-label ambiguity for the lesson table versus Appendix; verify against the original before approval. The official SOW gives teacher discretion on Project Lessons 88 and 160 and Language Awareness lessons; do not fill fixed SK/SP where SOW does not prescribe it.

## Open READY blockers

1. **Editorial structure:** 24 first-pass lesson flags still need human review for phase naming or explicit teacher/pupil action descriptions: 16, 20, 22, 23, 24, 26, 27, 29, 30, 31, 32, 33, 35, 41, 42, 43, 44, 45, 47, 48, 49, 50, 51, 61. Flags can be false positives (imperative teacher directions without the literal word Teacher); these require reading, not bulk blind replacement.
2. **Primary content:** Visual checks of every prescribed English Plus SB/TB/WB page, activity/exercise and BPK literature material are incomplete. Earlier filename mapping is not exercise-level verification.
3. **Audio:** 80 tracked audio filenames exist per earlier source audit, but recording content, correct lesson association and download links have not all been played or tested.
4. **RPT 2027:** Number/focus checks succeeded, but the source calendar/staging sheet remains BELUM FINAL. No live database synchronization or full subject plan approval was performed.
5. **Output:** The runtime Word/PDF one-page A4 export has **not** been validated across all 160 lessons, nor tested for Telegram/Web download parity.
6. **Approval:** Teacher approval is required lesson by lesson, including teacher-selected standards for Language Awareness and Project lessons.

## Second-pass remediation and re-read — current position

The 44 original screening alerts were **first-pass findings**, not unresolved defects. After targeted branch changes:

- 22/22 `ACTORS`-flagged drafts were edited to identify explicit **teacher assessment actions** and observable pupil outputs. Direct re-read of all 22 confirms teacher language, PBD, closure and DRAF are present.
- 2/2 `PHASE`-flagged drafts (16, 27) now have separate PBD and closure (same 60-minute totals). Both were re-read.
- 2/2 `WRONG_BPK` source-category errors (59, 66) corrected from the official SOW and selected scanned English Plus pages.
- 7/7 flagged duplicate Workbook notes removed (86, 89, 96, 100, 109, 133, 134).
- 2/2 `TIME` duration totals corrected (106, 108).
- 8/8 `GENERIC` placeholder objective/PBD flags in 152–159 replaced with lesson-specific measures.
- **1 official SOW discrepancy remains unresolved (Lesson 141, Writing 4.2.2 vs 4.2.4).** The Lesson 141 RPH includes an explicit approval hold; neither source has been silently overwritten.

**Mechanical screen: 43/44 initial alerting files remediated at textual level, 1 official code conflict held.** This is **not** a content-quality pass of the complete 160 lessons; unflagged lessons can still contain mistakes that automated checks cannot detect, and none is granted READY.

### Release blocker classification

**Blocking, must be verified:** content/step fidelity against SB/TB/Workbook or BPK primary-source pages; correct audio contents and link playback; teacher-selected standards or approved discrepancy resolution; all 160 one-page A4 actual runtime Word/PDF exports and Telegram/Web download parity; 2027 RPT final schedule and live curriculum alignment.

**Completed but insufficient alone:** existence/naming 160 files, SOW focus and RPT row correspondence 160/160, 43 textual remediations and selected-page scans.

The prior per-batch audit reports remain immutable historic first-pass snapshots; use this section as the current remediation ledger.

**Decision:** READY = 0 newly certified in this pass. This protects production teachers from unverified content. All fixes are on development branch only; no mutation to `main` or active DB.
