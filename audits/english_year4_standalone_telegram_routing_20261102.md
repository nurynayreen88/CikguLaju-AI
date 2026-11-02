# English Year 4 — standalone-to-Telegram routing audit (2026-11-02)

Status: **AUDIT ONLY — NOT READY FOR RELEASE**. This file does not change the master RPT, lesson plans, database or runtime.

## Verified against GitHub main

- Standalone lesson files exist at `rph_standalone/english/year4/lesson_001.md`, `lesson_014.md`, `lesson_040.md`, `lesson_080.md`, `lesson_100.md`, `lesson_120.md`, `lesson_159.md` and `lesson_160.md`.
- Lesson 1 lists Student's Book p.5, Teacher's Book p.18 and Class CD1 Track 3; the source itself records mapping limits.
- Lesson 14 is a Writing lesson about an email and punctuation. It explicitly does not prescribe a Workbook activity before printed page/task verification.
- Lessons 80 and 160 are teacher-selected project lessons; do not invent official SK/SP or impose Student's Book/Workbook/audio.
- The checked `app.py` blob has an English Year 3 standalone adapter reference but no direct `english_y4_standalone` or `year4/lesson_` reference. **This is not proof that no other Year 4 integration exists**.

## Required before any production merge

1. Trace the actual Telegram Year 4 lesson selection state through `_local_rph_text`, `_rph_rows`, PDF and Word generation. Confirm selected lesson number and year/subject normalization.
2. Inventory all 160 Year 4 lesson files and record missing/incomplete phases without rewriting existing verified lessons.
3. Implement a non-destructive, Year-4-only adapter **only if** the routing trace confirms it is needed. Support varying heading capitalization and phase labels, and prevent QA/source notes leaking into teaching phases.
4. Preserve verified Student's Book, Teacher's Book, Workbook and audio mappings; do not infer missing tracks or workbook pages.
5. Regression-test Lesson 1, 14, 80, 160, plus Year 2/3 unchanged; then generate and inspect Telegram Word and PDF.
6. Obtain explicit final verification before merging to `main`.

No production deployment is claimed by this audit.
