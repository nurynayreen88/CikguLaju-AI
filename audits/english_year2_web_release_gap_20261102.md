# English Year 2 — Web release gap audit (2026-11-02)

## Existing verified evidence

- Source: `staging/english-wb-isolated-20261031/audits/english_year2_001_040_sp_exhaustive_check_20261101.md`.
- Lessons 001–040: 40/40 main and complementary SK/SP pairs matched official SOW in prior audit.
- Lessons 022–024, 032–033, 035–040 (11): pending SOW phrases are stale **for SK/SP matching only**.
- The audit explicitly excludes detailed activity, textbook/workbook pages, audio, and PDF output.

## Current Web gate

- `web/english_release_gate.py` accepts only exact `**QA status:** READY FOR RELEASE`.
- Example Lesson 001 ends with a draft QA status and explicitly says not to publish as READY.
- Lesson 080 and 160 in prior staging also explicitly state NOT READY.

## Action without destructive changes

1. Preserve all existing RPH Markdown, SOW and DB records.
2. Reuse the 40/40 SK/SP audit; do not re-audit those pairs.
3. Separately verify activity and assessment specificity, SB/WB/audio references when applicable, and one-page A4 Word/PDF rendering.
4. Record an explicit per-lesson release decision only after all checks; never infer release from file existence or the SK/SP audit.
5. Keep the Web download gate fail-closed until an explicit release decision exists.

**Status:** Gap audit recorded; zero new lessons approved by this report.
