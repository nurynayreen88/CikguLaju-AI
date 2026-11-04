# English CikguLaju — Full RPH source-content QA, 4 November 2026

**Decision:** Year 2–6 **TECHNICAL STRUCTURE / SOW HEADER MATCH PASS**. **NOT PEDAGOGICAL FINAL READY**. Year 1 is separate legacy inventory pending KP2027.

## Method and source boundary

Read all files in `rph_standalone/english/year1` through `year6` from the PR's checked-out GitHub tree. Year 2–6 header SK/SP (Main and Complementary) were compared against the existing 800-row KPM SOW index. The independent existing row-to-native-Word/PDF regression also passed. Text patterns were scanned for repetitive instructions, explicit objectives and timing. This report does **not** independently verify all printed SB/TB/WB exercises, playable audio speech, individual classroom sign-off, or authenticated Telegram Word/PDF download.

Source audit: `tools/audit_english_800_text_quality_20261104.py`; GitHub Actions workflow `english-full-rph-content-audit-20261104.yml`; JSON artifact `english-960-rph-800-sow-full-content-audit` (14-day CI retention).

| English | Source files | Fixed official SOW pairs matched | Teacher-selected SOW | Explicit objective headings | Key follow-up |
|---|---:|---:|---:|---:|---|
| Year 2 | 160/160 | 160/160 | 0 | 160 | 47 headers retain obsolete “SOW verification pending” wording; verify source provenance before changing metadata |
| Year 3 | 160/160 | 160/160 | 0 | 2 | 158 without explicit objective header in *source Markdown*; 12 generic-phrase flags; seven source files below 1,000 characters |
| Year 4 | 160/160 | 150/150 | 10 | 7 | Many objectives supplied by guarded renderer; confirm source-linked final wording. Lesson 30 audio CD1/CD2 source conflict remains blocked |
| Year 5 | 160/160 | 151/151 | 9 | 160 | Lesson 29 and 30 list 60-minute duration but individual phase times are not stated. New draft release remains gated |
| Year 6 | 160/160 | 146/146 | 14 | 160 | 115 Lessons contain at least one generic phrase; many fixed-standard openings/closures repeat. No wholesale READY approval |
| **Year 2–6** | **800/800** | **767/767** | **33** | — | **0 critical technical structure/SOW-header mismatches** |

**Important interpretation:** Objective-heading counts measure source Markdown only; Year 3 and 4 can receive task-derived objectives through their native renderer. A missing heading is **not proof** the final document lacks an objective. Likewise, Workbook/audio keyword counts are **not** evidence that those resources are verified or delivered.

## Year 1 separate inventory (not included in Year 2–6 release gate)

Exactly 158/160 paths exist using the three-digit convention `lesson_001.md` to `lesson_160.md`: **Lesson 058 and 128 are absent at those paths**. Five additional nonstandard filenames `lesson_87.md`, `lesson_96.md`–`lesson_99.md` exist, plus a README. These are legacy Year 1 files, and neither their standards nor their timing can be promoted to KP2027 merely by renaming. Separate Year 1 curriculum redesign is required.

## Release blockers distinct from technical test results

1. Independently compare each outstanding Activity, instruction and exact printed page against SOW, Student's/Pupil's Book, Teacher's Book and Workbook.
2. Verify the *spoken content* of every assigned recording and actual Telegram Drive-file routing. **Year 4 Lesson 30**: Teacher's Book says **CD1 Track 29**; SOW says **CD2 Track 29**. The fail-closed safeguard must remain until proven.
3. Verify final teacher-facing Word and native PDF generation/download using a controlled authenticated Telegram account, including page count and quota/entitlement behaviour. Isolated PDF A4/row tests cannot prove live delivery.
4. Confirm teacher-selected DSKP Main/Complementary standards for the **33 optional** SOW lessons (Y4 10, Y5 9, Y6 14); suggested CikguLaju projects are not prescribed official SOW projects.
5. Approve individual lessons with exact-source checksums. Do not silently activate Year 5 drafts, alter user's billing/database records, or claim a blanket FINAL READY.

## Suggested repair order

- **Priority 1:** Correct 47 stale Year 2 SOW verification notes only after confirming original source, and tighten generic activities in 12 identified Year 3 lessons.
- **Priority 2:** Review Year 6's 115 generic wording flags lesson-by-lesson against actual relevant source tasks. Avoid replacing accurate lesson-specific activities with another generic template.
- **Priority 3:** Make Year 5 Lesson 29/30 phase time allocation explicit (not SOW-mandated), verify that the Year 3/4 renderer produces accurate measurable objectives and that teacher-facing QA notes are stripped.
- **Priority 4:** Resolve Y4 L30 recorded speech, then verify authenticated Telegram Word/native PDF delivery and optional teacher-choice standards.

**Safety:** This audit and its CI are read-only. No production app.py, Render deploy, Telegram callback, RPT PDF, subscription, Supabase/DB data, user quota or approval flags are modified.
