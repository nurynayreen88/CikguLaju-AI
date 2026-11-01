# CikguLaju AI — Non-textbook learning and assessment policy

**Scope:** All subjects and school years; applies to standalone RPH and their downloadable materials. Draft implementation policy for staging, pending full curriculum and release QA.

## Mandatory rule
If a lesson does not use a textbook or workbook, it **must** have two separate, substantive deliverables:
1. **Learning Materials**: teacher-facing instructions and actual pupil-facing resources for each required activity (e.g. original text, flashcards, dialogue, visual descriptions, phonics cards, manipulatives, guided tasks). Include materials and timing that correspond to the existing lesson plan.
2. **Assessment Materials**: actual pupil assessment task(s), directions, answer key or observable performance rubric, criteria tied to learning objectives and SK/SP, and a PBD record template.

A generic instruction such as “prepare flashcards”, “do an assessment”, or an empty worksheet **does not** count as complete.

## Lesson-type routing
- `NON_TEXTBOOK` or `TEACHER_DEVELOPED`: both Learning Materials and Assessment Materials required.
- `TEXTBOOK_NO_WORKBOOK`: keep textbook tasks and add assessment materials if they do not sufficiently assess the lesson's objectives.
- `TEXTBOOK_AND_WORKBOOK`: preserve verified book-based activities and provide extra materials only when the lesson needs them.
- `LANGUAGE_ARTS_OR_PERFORMANCE`: include the actual original text/song/chant if permitted and a performance rubric; never assume a workbook page is needed.

## Content QA gate
- Match lesson number, subject, year, SK/SP, objectives, success criteria, language skills, lesson activity sequence, and allocated time.
- Include all pupil prompts, teacher script or instructions, examples, scoring key/rubric, and printable record grid.
- Do not invent page numbers, official standards, audio tracks, or claim that a teacher-developed task is from a published source.
- Do not overwrite existing standalone RPH; attach materials separately and link to them after review.
- No `READY` without content verification, document render/print check, and delivery/download tests.
- Make both learning and assessment materials individually downloadable; “Download all” should include both.

## Current Year 2 example implementation
- Lesson 007: speaking cards and dialogue + independent listening/speaking PBD.
- Lesson 008: phonics cards and sort mat + six-item sound check and letter-naming assessment.
- Lesson 009: writing frames and word bank + editing/writing assessment and rubric.
- Lesson 010: original chant and gesture cards + performance and oral response rubric.

**Status:** Policy documented in staging; application to all lessons and bot download UI is not yet implemented.
