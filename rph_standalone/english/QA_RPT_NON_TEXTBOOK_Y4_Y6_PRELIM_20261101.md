# RPT English Years 4–6 — preliminary cross-source audit (2026-11-01)

Status: PARTIAL / NOT APPROVED. Read-only findings; not a DB migration.

## Sources inspected
- Connected Drive workbook: CikguLaju_English_Primary_Y4_Y6_DB_READY_CORRECTED_20260921 (a September 2026 export/snapshot, **not** proof of current live DB).
- GitHub staging standalone actual lesson files: English Year 4 Lessons 080, 096, 112, 128, 144, 160.
- No verified read of live database or most recent deployed RPT. No independent page-by-page official SOW reconciliation yet. Therefore none of the numbers below is a count of fully verified or corrected live records.

## Distinct lesson numbers in inspected spreadsheet
| Year | Distinct lesson numbers | NON-TEXTBOOK explicitly tagged | SOW_OPEN_TEACHER_SELECT explicitly tagged | Language Awareness (separate category) |
|---|---:|---:|---:|---:|
| 4 | 160 | 41 (includes projects 080,160) | 0 | 8 (016,032,048,064,096,112,128,144; all tagged TEXTBOOK) |
| 5 | 160 | 27 | 2 (088,160 projects) | 7 (016,034,052,070,106,124,142; lesson_type blank) |
| 6 | 160 | 44 (includes projects 080,160) | 4 (155–158, teacher-select) | 8 (016,032,048,064,096,112,128,144; lesson_type blank) |

Caution: Year 5 and Year 6 each occur four times per lesson number in the fetched multi-sheet text representation. Counts above deduplicate by (year,lesson_no), not by physical row. The empty lesson_type cells require source verification, not an automatic TEXTBOOK classification.

Year 4 NON-TEXTBOOK lesson numbers: 004,005,010,015,021,023,026,031,037,039,042,044,047,053,058,063,069,074,078,079,080,085,089,090,095,101,106,109,111,117,118,122,127,132,133,138,143,151,153,159,160.

Year 5 NON-TEXTBOOK lesson numbers: 005,010,015,021,027,033,039,045,051,057,063,069,075,081,087,093,099,105,111,117,123,129,135,141,147,153,159. Project/open: 088,160.

Year 6 NON-TEXTBOOK lesson numbers: 005,010,015,021,025,026,031,037,041,042,044,047,053,058,060,063,069,073,074,076,079,080,085,090,095,101,106,108,110,111,117,118,121,122,125,127,133,137,138,141,143,154,159,160. Other open teacher-selected: 155,156,157,158.

## Direct staging RPH observations (Year 4)
- Lesson 080 Project-Based Learning 1: teacher-selected topic and SP; explicit teacher/pupil actions, group plan, product and presentation; optional original planning resource; no compulsory workbook/audio.
- Lesson 160 Project-Based Learning 2: same SOW-flexible design; assessment depends on teacher-approved project and selected SP.
- Lessons 096,112,128,144 are Language Awareness revision, **not** Non-Textbook; they include revision/TB/SB references as available, teacher/pupil actions and self-assessment. Teacher-selected SP is not an official SOW assignment.
- All six remain unapproved; project SP, topic and criteria need teacher sign-off.

## Follow-up / release blockers
1. Compare current **live RPT and database** rows (year,lesson_no,lesson_type,focus,main/complementary CS/LS, references) against authoritative SOW PDFs, not merely this exported workbook.
2. Compare each target row against standalone RPH and actual resource; flag generic activity or non-observable assessment individually.
3. Preserve optional references only when actually specified in SOW. In particular, NON-TEXTBOOK can still have explicit Workbook reference: classification alone must never erase one.
4. Never invent CS/LS for teacher-select lessons; label proposals as suggestions.
5. Apply changes only in staging after source confirmation and user approval; do not overwrite DB or production RPT.

## Honest counts
- Distinct records identified in inspected spreadsheet: 480/480 (160 each).
- Explicitly NON-TEXTBOOK tagged: 112 (41+27+44); additional SOW_OPEN_TEACHER_SELECT: 6 (0+2+4).
- Language Awareness separately identified: 23 (8+7+8).
- Fully verified against official SOW + current live RPT + live DB + standalone: **0 completed in this audit**.
- Confirmed corrected in current live RPT/database by this audit: **0**.
- Needs manual cross-source verification: at least 118 non-textbook/open records; do **not** interpret as 118 confirmed errors.
