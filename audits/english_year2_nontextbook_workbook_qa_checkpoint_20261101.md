# English Year 2: Non-textbook and workbook material QA checkpoint (2026-11-01)

## Evidence examined
- Original `rph_standalone/english/year2/lesson_081.md`, `lesson_082.md`, `lesson_160.md` on staging.
- `resources/english/y2/workbook_verified_map.py` and prior official-SOW audit reports `audits/year2_081_090_sow_alignment_20261101.md` and `audits/year2_151_160_sow_alignment_20261101.md`.

## Findings
1. Lesson 081: Non-textbook, teacher-created sports-day listening script, cards, two individually assessed interpretations and two descriptions. Draft is actionable but the 25-minute Activity 2 says pupils select main idea, while the narrative says main-idea task is optional extension; reconcile objectives and pupil steps before READY.
2. Lesson 082: Non-textbook with original outfit cards, model dialogue, individual PBD rubric. **Potential workbook mapping error:** draft says `Workbook p.91, Activity 1` whereas verified mapping dictionary has no entry for lesson 082; mapping associates page 91 with lesson 079. Treat workbook reference as unverified; do not propagate to bot or overwrite original automatically. Exact page/activity must be checked.
3. Lesson 160: Non-textbook original beach rhyme and individual presentation assessment. Header reads `Language Arts 42`, whereas preceding series is `Language Arts 31`. This same label exists in internal SOW master; official SOW sequence verification required. Do not guess replacement.
4. Prior audit reports indicate paired learning and assessment resources committed for lessons 081–085, 090 and 151–160. This checkpoint has NOT independently opened every resource file or verified generated documents.
5. Workbook map source comments indicate `LINKED_VERIFIED` status derives from `bot_lesson_index`; verify whether its numeric pages are Student's Book pages rather than Workbook pages before using them as Workbook citations. Do not equate a numeric page mapping with a confirmed Workbook activity.

## Gate
- No READY designation. Complete independent checks against actual official SOW, Student's Book, Workbook, Teacher's Book and audio, plus rendering and bot QA.
- Original RPH, database and main branch unchanged.
