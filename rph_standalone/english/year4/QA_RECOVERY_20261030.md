# English Year 4 standalone — recovery checkpoint (2026-10-30)

Branch: `staging/english-year4-standalone-20261030`. Preserve all existing lesson files; do not replace the bank or merge to main before QA.

## Verified by direct GitHub file reads
- Existing files: lessons 001–024 (sampled 001–024 except 025 onwards), 040, 041, 060, 080, 081, 100, 120, 140, 159, 160. This is **not** proof of complete 160-file coverage.
- Lesson 001 has specific SOW/SB/TB/audio mapping, but states song-content listening verification and Word/PDF runtime tests pending.
- Lessons 013–019 and 022–024 exist, all retain draft/pending status.
- Basic keyword scan of lessons 013–019, 022–024 (presence only, NOT source verification):

| Lesson | SB keyword | TB keyword | CD/Track keyword | Draft/pending |
|---|---|---|---|---|
| 013 | yes | yes | yes | yes |
| 014 | no | no | no | yes |
| 015 | no | no | no | yes |
| 016 | no | no | no | yes |
| 017 | yes | yes | yes | yes |
| 018 | yes | yes | no | yes |
| 019 | yes | no | no | yes |
| 022 | no | no | yes | yes |
| 023 | no | no | no | yes |
| 024 | no | no | yes | yes |

A missing keyword does not prove that a reference is required or absent; review SOW lesson classification before deciding. A present keyword does not establish accuracy.

## Next safe batch
1. Inventory all 001–160 filenames and mark missing files (do not overwrite).
2. For each lesson, validate exact SOW activity and main/complementary SP; distinguish non-textbook lessons.
3. Verify actual Student's Book / Teacher's Book / Workbook pages and audio content; never infer tracks from sequence.
4. Refine teacher/pupil activities, learning objectives and PBD with lesson-specific evidence.
5. Run one-page A4 Word/PDF smoke tests; only then change lesson QA status.
6. Commit reviewed lesson changes to staging and merge after tests, preserving other subjects and runtime DB.

This file records recovery evidence only; it does not claim any lesson is newly approved or deployed.
