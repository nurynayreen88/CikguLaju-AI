# English Year 4 — Source and Workbook QA Register (31 October 2026)

**Branch:** `staging/english-year4-standalone-20261030`  
**Scope:** 160 standalone lesson drafts. This register records actual checks, not READY approval.

## Source inventory (located in connected Google Drive)

| Source | Drive file ID | Inspection status |
|---|---|---|
| Primary Year 4 SK SOW | `13Wefj9KN7z5YWt2Wk9dxmcE3pXS4o16S` | Text accessible in prior review; lesson mapping requires per-lesson confirmation |
| Get Smart Plus 4 Student's Book | `12IyGg-Mw3Pn38GxZGkVrqGkjMVJsgZfN` | File located; direct page inspection pending |
| Get Smart Plus 4 Teacher's Book | `1lBWc96e8DCIMSdxzRuLC7CissHL52q8v` | File located; direct page inspection pending |
| Get Smart Plus 4 Workbook | `1vFEGRSrG0ANTweKVOV-TDCAAqL0_i9FX` | File located (31,962,347 bytes); text fetch returned empty, so **page/activity mapping NOT verified** |

## Actual repository scan: Lessons 001–024

- 24 of 24 lesson Markdown files were fetched from the staging branch.
- 0 of 24 retain the earlier exact generic sentence: `Where a matching Workbook activity is available, pupils complete it to practise the language skills taught in this lesson.`
- Lessons 001–007 use different metadata layout from later lessons; absence of a `**Status:** DRAFT` field is **not** evidence of approval.
- Lessons 010, 015, 021 are literature/poetry lessons without the word `Workbook`; this is not by itself a defect.
- Lesson 016 has a Unit 1 self-assessment follow-up; no explicit Workbook reference.
- Track-number mentions in lesson files are **text references only** and do not prove audio files were listened to or matched.

## Verification gates before READY / main

1. Read the actual Workbook PDF pages and match each suitable lesson to a **verified page and activity**; do not invent page numbers. Literature, CLIL, revision and project lessons must be handled individually.
2. Cross-check each lesson against SOW, Student Book and Teacher's Book, including actual activity and page references.
3. Check audio file contents against the printed CD/track references, not track numbers alone.
4. Generate and inspect sample Word/PDF output for page fit, formatting and any duplicate follow-up sentences.
5. Keep staging DRAFT until these checks pass; do not modify main or the production database as a side effect of QA.

**Result:** Source discovery completed; initial 24-lesson generic-sentence scan completed; source-content and export verification remain pending.
