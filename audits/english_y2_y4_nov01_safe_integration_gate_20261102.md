# English Year 2–4 — Safe integration gate (2026-11-02)

Status: STAGING / REVIEW. This file is additive only. No RPH, RPT, audio mapping, student book, workbook, database, or production code is replaced.

## Existing sources to preserve
- staging/english-y2-safe-supplements-20261101: audits/english_year2_001_160_cross_batch_qa_checkpoint_20261101.md
- staging/english-wb-isolated-20261031: Year 2/3 workbook audits and isolated additions
- staging/english-year3-standalone-20261025: Year 3 standalone work
- staging/english-year4-standalone-20261030: Year 4 standalone work and 2026-11-01 non-textbook audit
- Google Drive: 33-lesson Y4–Y6 STAGING QA teacher-review ZIP (not automatically approved/READY).

## Mandatory non-destructive rules
1. Treat main as authoritative for already-published assets. Do not bulk merge branches, overwrite RPH files, or replace textbook/audio references.
2. Identify missing lessons or assets by (year, lesson_no, asset_type); compare contents and checksums before adding.
3. Keep Language Awareness distinct from Non-Textbook; do not invent official CS/LS or force workbook/audio onto teacher-selected PBL.
4. Preserve Year 2 lesson continuity: 118→119, 152→153, 150→155→160.
5. Stage 33 special-lesson worksheets separately as DRAFT QA; teacher approval required per lesson before READY.
6. Validate the latest live DB and runtime separately; September Drive exports do not prove current live state.

## Outstanding targeted checks
- Y2: Lesson 160 heading sequence and workbook/SOW reference issues, including Lesson 82.
- Y3: lesson-specific source mapping flagged for Lessons 6, 114, 125, 126 and 151; do not infer audio track from lesson number.
- Y4: non-textbook material availability and manual approval; preserve 160 existing lesson records.
- Compare each proposed file against main before any further commit.

## Release gate
NO READY / NO DB MIGRATION / NO BULK MERGE. This additive staging branch may be proposed via PR only after exact file-level diff and relevant tests; merge only reviewed additions, not whole source branches.
