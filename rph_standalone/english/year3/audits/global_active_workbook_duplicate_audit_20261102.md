# English Year 3 — Global Active Workbook Assignment Audit
**Date:** 2026-11-02  
**Scope:** `rph_standalone/english/year3/lesson_001.md`–`lesson_160.md` on GitHub `main`.

## Audit rule
- Inspect the section headed **PBD**, **Assessment / PBD**, or **PBD / Reinforcement**.
- Extract only active pupil instructions matching `**Pupils:** Pupils complete Workbook p.<page>, Activity <number>`.
- Identify a collision only when **both printed Workbook page and activity number** match.
- Exclude historical mentions of exercises that the RPH explicitly says **not** to repeat.
- Do not equate same Workbook page with a duplicate if activity numbers differ.

## Results
All 160 Lesson files were fetched for the targeted active-assignment check. **No duplicate page + activity pair was found among the pupil instructions matching the exact extraction pattern.**

This is **not** a claim that every Workbook task is unique: instructions with other verbs, punctuation, headings, or layouts are outside this exact-match pass. No page-level verification against the original Workbook or SOW/TB was performed in this pass.

## Previously resolved collision groups
- Lessons 4/14: Workbook p6 Activity 2
- Lessons 17/18: p10 Activity 1
- Lessons 24/25: p12 Activity 1
- Lessons 38/41: p19 Activity 2
- Lessons 39/44: p21 Activity 2
- Lessons 43/48: p24 Activity 1
- Lessons 45/51: p31 Activity 1
- Lessons 50/56: p30 Activity 2
- Lessons 66/70/76: p37 Activity 2
- Lessons 77/78: p40 Activity 1
- Lessons 83/86/87: p45 Activity 2
- Lessons 99/102/103: p53 Activity 2
- Lessons 116/123: p63 Activity 1
- Lessons 119/124: p63 Activity 2
- Lessons 120/121: p62 Activity 2
- Lessons 130/134: p68 Activity 3
- Lessons 135/140: p71 Activity 1
- Lessons 151/156: p79 Activity 2
- Lessons 152/157: p80 Activity 1
- Lessons 153/155: p80 Activity 2

## Release gates
1. Broaden extraction to **all** teacher/pupil Workbook assignments, not only `Pupils complete` phrasing.
2. Verify page/activity alignment against the actual original Workbook, SOW and Teacher's Book.
3. Confirm that original CikguLaju material files are present, appropriately skill-specific and linked.
4. Render Word/PDF and inspect pagination, fonts, layout, teacher keys and student-facing content.
5. Keep RPT master and DB untouched; approve lesson-by-lesson before READY.

**Status: PARTIAL AUDIT — NOT READY FOR RELEASE.**
