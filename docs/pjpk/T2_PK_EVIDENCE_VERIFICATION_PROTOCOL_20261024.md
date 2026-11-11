# Tahun 2 Pendidikan Kesihatan — source-first evidence protocol

Scope: 18 editorial RPH (7 with recorded SP codes; 11 with standards deliberately unset). This document is a work instruction, not a source verification or production approval.

1. Match each `entry_id` to the original 161-row source-gate identity. Never treat a reference-only record as a PdP.
2. Read the authoritative Tahun 2 DSKP page for each lesson and record exact SK and SP codes **and verbatim text**, printed page and source identifier. A previously recorded SP code alone is insufficient; never infer SK/SP from topic labels.
3. Inspect the matching textbook page visually when extracted text is empty; record printed and physical PDF page separately. Record unavailable evidence as pending, not as a guessed page.
4. Identify the exact RPT PdP slot and year, not merely a similar theme or week. Preserve the original sequence and distinguish PJ from PK.
5. Check lesson objectives, subject-specific activities, assessment, age appropriateness and reference fields against the evidence. Render A4 and verify one-page layout and readability; editorial preview success is not a runtime pass.
6. Run the actual Telegram selection-to-RPH generation smoke test for each approved row, including missing-source and wrong-year rejection cases. Keep all flags false until their specific evidence is attached.
7. Only promote rows with all gates passed using additive, backed-up database changes. Preserve legacy DB and menu functionality. Production deployment requires separate verification.

Current checkpoint: the seven-record and eleven-record JSON files are editorial staging only, `production_ready=false`; do not flip flags as a batch. Generate the 18-row evidence workqueue using `python -m scripts.pjpk_t2_pk_evidence_queue OUTPUT.csv`.
