# English Year 4 — Workbook integration gap check (14 TB-audio-mapped lessons)

**Method:** Read-only text inspection of the current standalone RPH on staging. This check identifies explicit Workbook references, not whether a Workbook task is pedagogically required. No new Workbook pages were visually verified.

| Lesson | Explicit Workbook reference in RPH | Next action |
|---|---|---|
| 030 | Explicitly withheld pending printed page/activity verification | Verify source before assigning |
| 032 | None | Review revision/self-assessment requirements |
| 065 | WB p.39 Activity 1 | Retain as written practice; listening assessed separately |
| 097 | Explicitly withheld pending verification | Verify source before assigning |
| 098 | None | Check printed WB task and SOW before addition |
| 102 | None | Check printed WB task and SOW before addition |
| 103 | None | Check printed WB task and SOW before addition |
| 104 | None | Check printed WB task and SOW before addition |
| 105 | None | Check printed WB task and SOW before addition |
| 107 | None | Check printed WB task and SOW before addition |
| 110 | WB p.61 Activity 2 | Retain written grammar practice and independent writing PBD |
| 123 | None | Phonics lesson: verify whether a WB activity is prescribed |
| 129 | WB p.77 Activity 1 | Retain written vocabulary practice; listening assessed separately |
| 134 | None | Check printed WB task and SOW before addition |

**Observed:** 3 of 14 explicitly assign a numbered WB page/activity (065, 110, 129); 2 explicitly prohibit inventing one (030, 097); 9 have no Workbook reference. Missing references are **not** evidence that a WB task is required or that the lesson is incomplete.

**Release discipline:** Keep existing RPH intact. For any verified new WB task, propose only a concise English-language sentence in the appropriate lesson activity/assessment area; do not overwrite other activities, invent page numbers, or substitute WB written work for listening/speaking evidence. Seek review before READY/main merge.

## Direct Workbook source inspection (31 October 2026)

Downloaded the original `Get Smart Plus 4 Workbook.pdf` from the existing Drive source (109 PDF pages; scanned image pages, no selectable text in sampled pages). Visually inspected **PDF page 20**, which is **printed Workbook page 21**. This page is headed **“In the past 3 — Do a quiz”** and contains a crossword, Past Simple fill-in sentences and three questions about yesterday. It is **not** evidence for a Workbook assignment in Lesson 030 (“My Week”, Writing 6). Do not infer Workbook printed-page numbering from the PDF index or assign this page to Lesson 030. Further page-by-page source inspection is needed before adding verified Workbook tasks to the nine lessons without explicit references.

## Unit 2 My Week — direct visual Workbook review

The source `Get Smart Plus 4 Workbook.pdf` (Google Drive file `1vFEGRSrG0ANTweKVOV-TDCAAqL0_i9FX`) was inspected visually, rather than relying on extracted text. **PDF page numbers are one less than printed Workbook page numbers in these samples.**

| PDF page (1-based) | Printed WB page | Printed heading | Actual activity evidence |
|---|---|---|---|
| 11 | 12 | My week — Sing a song | Crossword / song-related words and follow-up |
| 12 | 13 | Smart kids | Activity 1 timetable reading and ticking pupils; Activity 2 written frequency answers |
| 13 | 14 | Our world | Activity 1: write household-duty sentences from six pictures; Activity 2: answer three questions about personal daily/weekend duties |
| 14 | 15 | Let's play | Activity 1 listening and numbering five pictures; Activity 2 written answers about duties; Activity 3 sentences using `have to` or `don't have to` |
| 24 | 25 | Project | Past-trip tasks; **not** Unit 2 My Week |

**Lesson 030 relevance:** Printed WB p.14 Activity 1 provides independently observed household-duty sentence writing and is a **candidate** for the lesson's Writing 4.3.2 practice; however the current RPH focuses on correctly spelling chore cards and SB p.20 Activities 1–2. This candidate is **not yet a confirmed lesson-level TB/SOW assignment**. Printed WB p.15 Activity 3 is also a possible grammar/writing extension but has not been source-mapped to Lesson 030. Do not alter the existing lesson or claim that either is required until TB/SOW sequencing is checked.

**Assessment:** Printed WB p.15 Activity 1 is listening-based, so a written answer alone should not replace observation of the recording for Listening 1.2.5. No MP3 playback was verified in this inspection.

## Lesson 030 — SOW comparison and staging RPH change

Directly checked the KPM Year 4 SOW section **LESSON: 30 (Writing 6)** (Scheme of Work p.66). It prescribes SB p.20 Activities 1–2 and TB pp.38–39; **no Workbook page is prescribed**. Its printed lesson outline says **“CD2, Track 29”** for Activity 2, which conflicts with the separately recorded TB-verified **CD1 Track 29**. Preserve this discrepancy for source reinspection; do not silently substitute SOW CD2 or treat the CD assignment as fully reconciled.

A **single optional Workbook sentence** was added to staging `lesson_030.md` in commit `1ca15ddd1fa48ab0be1a47143911fa9e2fc3d57d`: printed WB p.14 Activity 1, household-duty sentences from pictures, with spelling checked. This task was visually observed in the Workbook but **is an optional supplementary exercise, not a SOW/TB-prescribed lesson assignment**. Existing SB activities, listening evidence, and DRAFT status were preserved.

**Open gate:** Inspect TB p.39 directly to resolve the CD1/CD2 discrepancy; check time allocation before considering optional WB work for production. Audio playback and Telegram delivery remain untested.

## Lesson 030 — direct Teacher's Book visual resolution

**Source:** Original scanned `Get Smart Plus 4 Teacher's Book.pdf` (Drive ID `1lBWc96e8DCIMSdxzRuLC7CissHL52q8v`), **PDF page 25 / printed TB page 39**, visually inspected on 31 October 2026. The preceding PDF page 24 is printed TB page 38.

- TB p.39 **Activity 2: “Class CD1 - Track 29”** (Student's Book p.20 listening task). This confirms the existing staging RPH CD1 Track 29 mapping.
- TB p.39 **Workbook Activity 1: “Class CD1 - Track 30”**, followed by Workbook Activities 2 and 3. Track 30 belongs to the Workbook activity; it must **not** replace the SB Activity 2 Track 29.
- KPM SOW Lesson 030 prints “CD2, Track 29”; this conflicts with the directly inspected TB page. The discrepancy is **resolved for the current RPH's SB activity in favour of the original TB CD1 Track 29**; retain the SOW mismatch in provenance.
- Printed WB p.14 Activity 1 was visually inspected previously and is an optional writing extension in the current RPH, not a SOW-prescribed activity. Do not treat its listening component as independently playback-verified.

**Remaining:** Verify CD1 Track 29 and Track 30 MP3 playback and Telegram access; review Word/PDF output. Keep DRAFT until those gates and approval.

## Lesson 030 — Drive MP3 metadata and link-permission check

Checked both MP3s directly using Google Drive file metadata, against the existing `QA_CLASS_CD_ASSET_MANIFEST_20261031.json` entries:

| TB activity | Disc/track | Drive ID | Drive filename | Size (bytes) | Permissions |
|---|---|---|---|---:|---|
| SB Activity 2 (TB p.39) | CD1 Track 29 | `15tyBPsUwd5z9AknoOOUIiaTN6QT-Xrct` | `29 Track 29.mp3` | 218335 | anyone: reader |
| WB Activity 1 (TB p.39) | CD1 Track 30 | `1MhXoN--u1W1Rv7eSxVt3ujx3WgdEZfLl` | `30 Track 30.mp3` | 1117804 | anyone: reader |

The returned Drive metadata agrees with the manifest IDs and sizes, and both files expose **anyone-with-link reader** permissions. This is **not** an anonymous browser download test, MP3 decode/listening verification, or Telegram `sendAudio` test. Do not mark audio delivery READY based on these permissions alone.

**Remaining checks:** inspect actual audio content and duration; test unauthenticated retrieval; test Telegram bot delivery and generated Word/PDF before approval.

## Lesson 030 — Workbook page/activity reconciliation (direct PDF images)

Original Workbook PDF page 13 shows **printed p.14 Activity 1**, a six-picture written *have to* task, and Activity 2, three personal written answers. Original PDF page 14 shows **printed p.15 Activity 1**, *Listen and number (1–5)*, plus Activity 2 questions and Activity 3 *have to / don't have to*. These are distinct exercises. The RPH's optional written WB p.14 Activity 1 is correctly identified as writing; TB p.39's WB Activity 1 with **CD1 Track 30** refers to the listening exercise on printed **WB p.15**, not the p.14 writing exercise. The existing SB listening **CD1 Track 29** remains unchanged. Direct images checked 31 October 2026; MP3 speech-content match and Telegram delivery remain unverified.

## Lesson 032 — direct Teacher's Book page verification

Original scanned Teacher's Book PDF pages 32–33 show **printed TB pp.46–47**. TB p.46, Revision 2, Activity 1 explicitly specifies **Class CD1 Track 35** and Student's Book **p.26**. Pupils listen and match each child to two jobs; Activity 2 asks pupils to answer personal questions and ask a friend. TB p.47 contains answer keys for **Workbook Activities 1–3**, but does not print the corresponding WB page number on this spread. Therefore the current `lesson_032.md` CD1 Track 35 is **TB-confirmed**, and the WB page/activity assignment is **not yet independently verified**. Do not insert a guessed WB page or replace the SB listening task. Telegram audio delivery and Word/PDF QA remain pending; status DRAFT.
