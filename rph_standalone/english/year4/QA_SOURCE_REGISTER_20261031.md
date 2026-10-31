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

## Visual Workbook matching — Unit 3 and Unit 4 (additional batch)

A new visual contact sheet was rendered from PDF pages 18–35 of the scanned Workbook. The printed page numbers were read from the actual images. **Important correction:** previous notes about a universal PDF-page/printed-page offset are not reliable; use the visible printed page number for each activity, not an inferred offset. No automatic page-number conversion is approved.

### RPH files updated

| Unit | Lesson | Printed Workbook page | Visually observed activity | Use |
|---|---:|---:|---|---|
| 3 | 033 | 22 | Smart kids past-tense question task | Optional past-question practice |
| 3 | 034 | 24 | Let's play, questions about yesterday | Speaking practice |
| 3 | 035 | 23 | Our world, Ancient Egypt vocabulary | Optional reading support |
| 3 | 036 | 24 | Let's play, past-simple questions | Optional writing practice |
| 3 | 040 | 26 | Story time, past-events comprehension | Optional reading practice |
| 3 | 041 | 26 | Story time, past-tense sentence completion | Optional writing practice |
| 4 | 049 | 30 | Sing a song, celebrations vocabulary | Vocabulary support |
| 4 | 050 | 30 | Sing a song, ordinal numbers | Speaking about dates |
| 4 | 051 | 35 | Story time, reading/matching | Optional comprehension |
| 4 | 052 | 31 | Smart kids, picture prompts | Writing support |
| 4 | 055 | 32 | Our world, future-plans prompts | Speaking support |
| 4 | 056 | 35 | Story time, reading/matching | Optional comprehension |

**12 lesson files were updated.** The original teaching sequence was preserved; only existing generic Workbook follow-up sentences were replaced. These Workbook activities are optional aligned supplements, not verified mandatory SOW prescriptions. No audio-file contents were independently verified, and no Word/PDF generation was tested in this batch. All changes remain on staging.

## Unit 5 Workbook matching — continuation

Visual source: scanned Get Smart Plus 4 Workbook, printed pages 39–44, previously inspected. Six new successful lesson edits across two batches: 065 (p.39 Activity 1), 066 (p.39 Activity 2), 067 (p.40 Activities 1–2), 068 (p.40 Activity 3), 070 (p.41 Activity 1), 071 (p.41 Activity 2). Further two lesson edits: 073 (p.43 healthy-eating diary project), 075 (p.44 healthy-eating reading passage). These are **optional follow-up activities**, not SOW-mandated page assignments. The prior safety-tool failures for 066 and 068 were resolved and both files are now committed. Total new lesson edits in this continuation: **4 (066, 068, 073, 075)**. Lessons 074, 078, 079 and 080 are literature, teacher-selected or project lessons and should not receive invented Workbook pages. Audio and export QA remain outstanding. All changes are on staging.

## Unit 6 Workbook — visually inspected batch

Scanned Workbook PDF pages 46–59 were rendered for direct visual inspection. The printed Unit 6 pages 50–56 show: road-safety song/picture (p.50), transport and timetable exercises (p.51), transport vocabulary and sentences (p.52), transport picture prompts (p.53), project/crossword (p.54), Story time dialogue and questions (p.55), and Revision (p.56). The sample also includes the beginning of Unit 7.

Nine lesson files were changed with **optional**, lesson-relevant Workbook follow-ups:

| Lesson | Printed Workbook page | Purpose |
|---|---:|---|
| 081 | 50 | Road safety identification |
| 082 | 50 | Road safety rules |
| 083 | 51 | Transport and timetable reading |
| 086 | 52 | Travel vocabulary |
| 087 | 53 | Transport questions |
| 088 | 54 | Project vocabulary and reading |
| 091 | 53 | Transport word review |
| 092 | 56 | Revision prompts for speaking |
| 093 | 55 | Story time reading questions |

This is **not** verification of audio recordings or a claim that the SOW mandates these Workbook tasks. Preserve literature/CLIL/project exceptions. No READY approval or main merge.

## Workbook Assessment / PBD formatting QA — 31 October continuation

Instruction: retain original assessment evidence and teaching activities; use Workbook only where its actual task is relevant, with separate Teacher and Pupils lines under existing PBD section. No unverified activity numbers are to be invented. In this batch, Lesson 002, 073 and 075 were converted to the specific Workbook assessment format. Lesson 017, 018, 019, 025 and 027 were corrected to separate Teacher and Pupils formatting. Lesson 033–036, 040–041 and 049–052, 055–056 were inspected and already have separate Teacher and Pupils Workbook instructions. No audio or final 10-minute timing validation is claimed. Keep DRAFT.

## Workbook relevance cleanup — Lessons 057–105

A review of existing generic Workbook references found no verified page/activity mapping for the following lessons in the inspected source material. Generic conditional claims ("use a suitable Workbook activity, if available") were removed, while the original PBD evidence and teaching tasks were preserved:

- Unit 4: Lessons 057, 059, 060, 061, 062, 064.
- Unit 5: Lessons 072, 076, 077.
- Unit 6: Lesson 094.
- Unit 7: Lessons 097, 098, 099, 100, 102, 103, 104, 105.

Literature/poetry lessons and lessons already explicitly using a story guide, CCL worksheets, or self-assessment were not assigned invented Workbook pages (063, 069, 074, 078, 079, 080, 095, 096, 101). This cleanup does **not** assert that these lessons can never use Workbook; it means no sufficiently verified relevant activity/page was established in this pass. Preserve existing Assessment/PBD content. Audio and Word/PDF timing/export QA remain outstanding. Staging only; DRAFT.

## Unit 7–8 generic Workbook reference cleanup — next batch

Reviewed Lessons 106–121. Literature lessons 106, 111, 117 already refer to The Jungle Book Teaching Guidebook and were not assigned generic Workbook tasks. Lesson 109 uses a teacher-prepared recycling reading text; Lesson 112 is Unit 7 self-assessment; Lesson 118 uses a teacher-prepared listening text; these retain their source-specific assessment and no Workbook page is asserted. Generic unverified Workbook suggestions were removed from Lessons **107, 108, 110, 113, 114, 115, 116, 119, 120 and 121**. No page/activity number was invented. Original PBD and teaching sequence remain unchanged. Specific Workbook task matching requires visual inspection of the corresponding printed Workbook pages before insertion. Audio/Word/PDF and timing QA remain pending; DRAFT, staging only.

## Lessons 122–160 — Workbook relevance cleanup

Removed unverified generic Workbook suggestions from 24 lessons: 123–126, 129–131, 134–137, 139–142, 145–148, 150, 152, 155–157. Existing PBD and Activity 1/2 remain intact. Literature, teacher-selected, project and revision lessons retain their original source-specific assessments. This is **not** a verified page-by-page Workbook matching pass; the scanned Workbook and precise activity instructions still require inspection before any new Workbook mapping. DRAFT; do not merge main or mark READY.
