# English Year 1 — Teacher's Book Activity Audit (25 October 2026)

Read-only source review of the five existing `data/teacher_book_guidance_y1_batch*.json` files on `main`.

| Source batch | Records | Provenance |
|---|---:|---|
| Friends / batch01 | 6 | VERIFIED_TB_SCAN |
| At School / batch02 | 8 | VERIFIED_TB_SCAN |
| Let's Play! / batch03 | 12 | VERIFIED_TB_SCAN |
| Pet Show / batch04 | 13 | SOURCE_ALIGNED_GUIDANCE |
| Lunchtime / batch05 | 12 | VERIFIED_MAPPING_GUIDANCE |
| **Total** | **51** | **26 direct TB scan, 25 mapped guidance** |

- 51 unique year/lesson keys; no duplicate keys across the five files.
- 35 records lack at least one of `warm_up`, `student_book_procedure`, `checking_feedback`, `ending_lesson`.
- This count measures missing source fields, not teaching quality or PDF fitness.
- No claim that the remaining 16 records have passed pedagogical or A4 QA.
- The source material covers selected Year 1 lessons only; it does not establish full Year 1–6 coverage.

## Implementation guardrails
1. Preserve existing lesson sequence, SOW, SK/SP, and original databases.
2. Keep direct TB scan verification distinct from mapping-based guidance.
3. Do not invent Teacher's Book instructions, page numbers, or audio tracks.
4. For missing warm-up/closure, prepare explicitly labelled original teacher-developed proposals grounded in the lesson focus, subject to review.
5. Mark each activity phase's provenance and review status.
6. Generate standalone RPH only as drafts until teacher/pedagogical and A4 QA pass.
