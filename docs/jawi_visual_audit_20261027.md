# Jawi PDF visual audit — 2026-10-27

## Provenance
- PR #43, head `31dca5f4816804ebe17aaf5e1aa43305818b7dbb`.
- Actions run `40474975731`; artifact `jawi-actual-flowable-pdf` (`12720355620`).
- PDF inspected: `jawi_renderer_12class_v2639_full_rph_layout.pdf`.
- SHA-256: `77624d42cc6a76a2a47218725cc4069d277977a64934df3f0e032c5da8162ba9`.

## Observations (rendered page image, 2× scale)
- A4 portrait, 595.28 × 841.89 pt, exactly one page.
- 11 table rows / sections; 22 embedded text images; no image bounding-box overflow detected.
- Glyphs appear connected and right-to-left in the rendered sample; no obvious clipped text within the table in this sample.
- All text is image-based (zero selectable characters). This limits text selection, search, and accessibility.
- **Not curriculum verification:** Content is synthetic. The runner extracts classes and the v26.39 resolver body and supplies controlled replacements for other helpers and font discovery. It is *not* the complete runtime or a DB-backed RPH.

## Release gate
**NOT APPROVED for merge/deploy.** A production-code-path PDF from verified existing Year 1–6 Pendidikan Islam DB SK/SP and lesson-specific content is still needed, followed by a real bot PDF comparison. Maintain read-only DB handling and do not silently correct/replace verified Jawi code points.
