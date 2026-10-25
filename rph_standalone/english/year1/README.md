# English Year 1 — Standalone RPH index

**Coverage:** Lesson 001–160. One Markdown file per lesson at `lesson_NNN.md`.

**Purpose:** A practical, fast-to-review bank of Year 1 English lesson plans, not yet a production-ready RPH output.

## Fast pre-release check

1. Confirm all 160 files exist and lesson number, unit, main SK/SP and complementary SK/SP match `data/english_y1y2_sow_master_320.json`.
2. Each lesson needs an observable objective, teacher and pupil actions, set induction, activities, PBD and closure. Where sections differ, preserve existing verified Teacher's Book instructions.
3. Distinguish provenance: `VERIFIED_TB_SCAN` means Teacher's Book evidence was checked; `SOURCE_ALIGNED_GUIDANCE`, `VERIFIED_MAPPING_GUIDANCE` and `SOW_MAPPED_ONLY` are **not** equivalent to full Teacher's Book verification.
4. Do not invent textbook page numbers, audio tracks, activity numbers or Teacher's Book steps.
5. Test the existing PDF renderer on a small sample of lesson files, then confirm A4 single-page layout before making the bank available to users.

## Release policy

The lesson files on this staging branch are editorial source material. Creating them does **not** integrate them into the Telegram bot. Preserve the existing database and generator; keep production unchanged until integration and a smoke test succeed. No automatic merge or deployment.

## Recommended sample

- Lesson 001 — SOW-mapped Friends speaking draft
- Lesson 016 — Teacher's Book-verified Friends reading plan
- Lesson 080 — SOW-mapped Pet Show language arts draft
- Lesson 150 — SOW-mapped Lunchtime review
- Lesson 160 — SOW-mapped Year 1 revision
