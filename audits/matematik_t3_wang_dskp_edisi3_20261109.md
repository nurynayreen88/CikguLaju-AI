# Audit guru Matematik Tahun 3 - Wang / PdP 060

9 November 2026. STATUS: STAGING REVIEW ONLY. Do not deploy the editorial samples as live RPH without verifying the school/teacher curriculum edition and original source.

## Problems verified against the test PDF

- Standard Kandungan is duplicated: 4.4 4.4.
- The objective is generic (shows knowledge or skills based on the standard), not measurable.
- The success criteria give no specific count or evidence of individual attainment.
- Phase minutes are 5 + 12 + 18 + 20 + 5 + 5 = 65, whereas the timetable states 60 minutes.
- The activities do not demonstrate coverage of all factor cases 1 digit, 10, 100 and 1000.
- Class name 4 Ikhlas is a deliberate teacher test entry. This is NOT a curriculum error.
- Do not invent textbook/workbook pages without checking the actual school edition.

## Critical academic edition split

| Curriculum | SK | SP | Scope |
| --- | --- | --- | --- |
| Original KSSR DSKP Semakan 2017 (Tahun 3), printed p.48 | 4.4 Darab wang | 4.4.1 | Multiply money values by one digit, 10, 100, 1000, products up to RM10,000 |
| KSSR Penjajaran Edisi 3 Matematik Tahap I (Tahun 3), printed p.49 | 4.2 Darab dan bahagi wang | 4.2.1 | Multiply AND divide money values; products up to RM10,000 |

The Malaysian Ministry of Education's Surat Siaran KPM Bil. 6 Tahun 2024 expressly says Edisi 3 is an OPTION and can be used alongside DSKP 2017. The two code sets are NOT interchangeable. Do not substitute the Edisi 3 code when the school RPT is based on original DSKP, or vice versa.

Official circular: https://www.moe.gov.my/storage/files/shares/pekeliling_dan_garis_panduan/surat_siaran/bahagian-pengurusan-sekolah-harian/Surat%20Siaran%20KPM%20Bil.%206%202024%20Pelaksanaan%20Dokumen%20Penjajaran%20Kurikulum%20Standard%20Sekolah%20Rendah%20Edisi%203%20Sains%20Dan%20Math%20Tahap%201.pdf

DSKP KSSR Matematik Tahun 3: https://asiemodel.net/wp-content/uploads/2022/08/DSKP-KSSR-SEMAKAN-2017-MATEMATIK-TAHUN-3.pdf

Penjajaran Edisi 3 Matematik Tahap I: https://ecentral.my/wp-content/uploads/2024/09/DOKUMEN-PENJAJARAN_KSSR-MATEMATIK-TAHAP-1_EDISI-3-compressed.pdf

## Pedagogical exemplar

Two independent one-page A4 Word/PDF examples were created in this review session from a shared structured source, both retaining the teacher's trial class and date. The original DSKP version focuses only on darab wang; the Edisi 3 version covers both darab and bahagi. Each has explicit learning objectives, measurable success criteria, 5+10+15+15+10+5 = 60 minute activities, teacher/pupil actions, individual PBD, differentiation and teacher reflection. The example documents were supplied as conversation attachments, not placed in the production catalog.

## Technical audit gate

The read-only script tools/rph_mathematics_year3_curriculum_audit_20261109.py checks:
- edition selection, exact SK/SP codes and duplicated SK;
- generic or unmeasurable objectives and criteria;
- duration and phase totals, teacher and pupil actions;
- evidence of operations and 10/100/1000 factors;
- unverified textbook page labels.

Even if the tests pass, status is EDITORIAL_REVIEW_REQUIRED and publication_ready is always false. It is not an academic score.

## Expansion to other subjects

Use the existing audit rubric from audits/rph80_program_20261107.md:
- 25 marks: SK/SP exact source and edition
- 25 marks: textbook/workbook/RPT correct pages and editions
- 25 marks: objective, activities, pupil actions, PBD evidence
- 15 marks: Word/PDF 1-page A4, activity numbering and typography
- 10 marks: authenticated, source-equal Web/Telegram availability and download

Any fatal SK/SP, book reference, student safety or false source assertion must remain HOLD regardless of an aggregate score. Explicit subject-by-subject human verification is needed before activating content. This PR has NO impact on app.py, master SQLite, Supabase, quota, billing, Telegram, or Render.
