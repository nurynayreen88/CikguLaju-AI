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

## Direct visual inspection of Workbook PDF (31 October 2026, second pass)

The 109-page scanned Workbook PDF was downloaded and opened. Embedded selectable text is absent, so visual page inspection is required; this is **not** a text-extraction failure of the file itself. Sampled PDF pages 1, 5, 10, 15, 25, 35, 45, 55, 65, 75, 85 and 95 were rendered and visually inspected.

| PDF page (1-based) | Printed Workbook page | Observed content | Scope of verification |
|---|---|---|---|
| 1 | Cover | Get Smart Plus 4 Workbook cover | Direct visual |
| 5 | 4 | Unit 1 *Let's play*, activities about actions and sentence writing | Direct visual |
| 10 | 9 | Unit 1 *Now I can 1* self-check, countries and nationalities | Direct visual |
| 15 | 14 | Unit 2 *Project*, household chores survey/chart | Direct visual |
| 25 | 24 | Unit 3 *Story time*, story comprehension | Direct visual |
| 35 | 34 | Unit 4 *Revision*, ordinal numbers and weekend schedule | Direct visual |
| 45 | 44 | Unit 5 *Vegetarians* reading passage and questions | Direct visual |
| 55 | 54 | Unit 6 *Revision*, transport vocabulary and comprehension | Direct visual |
| 65 | 64 | Earth Day reading and questions | Direct visual |
| 75 | 74 | Animal vocabulary / *Now I can 8* | Direct visual |
| 85 | 84 | Unit 10 *What's the matter?*, song and questions | Direct visual |
| 95 | 94 | Illustrated *What's the matter?* board-game page | Direct visual |

**Important:** The sampled internal pages show printed page number = PDF page number − 1. This relationship is observed in the samples, not a substitute for checking every page. These are **confirmed page-content observations**, not yet verified lesson-to-Workbook activity assignments. Do not automatically assign them to RPH Lessons without matching each lesson objective and SOW/TB. No production changes or READY approval were made.

## Workbook activity matching — verified visual sample (batch 31 October 2026)

The scanned Workbook was visually reviewed across PDF pages 2–17 (printed pages 3–18). The following lesson RPH files were **actually updated** with matching Workbook page/activity references, retaining their original teaching sequence:

| RPH Lesson | Printed Workbook page | Workbook task / use | Qualification |
|---|---:|---|---|
| 002 | 4 | Activity 2, country/nationality questions | Follow-up practice |
| 004 | 4 | Activity 3, own country/nationality writing | Optional supplement to non-textbook lesson |
| 009 | 5 | Activity 1, adverbs of frequency and routines | Writing follow-up |
| 016 | 9 | Now I Can 1, self-assessment | Optional Unit 1 check |
| 017 | 11 | Activity 1, school-subject crossword | Vocabulary follow-up; **not an audio replacement** |
| 018 | 12 | Activity 1, timetable and school subjects | Support for spoken questions |
| 019 | 15 | Activity 1, school-story questions | Reading follow-up |
| 024 | 12 | Activity 1, household-chores picture prompts | Vocabulary support |
| 025 | 14 | Project Activity 1, household-chores survey chart | Optional writing support |
| 027 | 13 | Activity 1, household-chores listening/numbering | Optional follow-up; audio mapping not yet checked |

**Scope:** 10 lesson files changed in this batch. These are visually grounded **suggested supplemental activities**; not claims that SOW requires those exact Workbook pages. Audio recordings and the remaining 150 lesson-to-Workbook matches are not yet independently verified. The source PDF is scanned (no embedded selectable text); do not infer page numbers from a global offset without visual confirmation. Staging only; not READY.
