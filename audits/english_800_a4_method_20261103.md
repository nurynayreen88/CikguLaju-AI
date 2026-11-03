# 800 English RPH A4 full audit (3 Nov 2026)

Audit source: all 160 English Lessons for each of Years 2–6. Uses exact AST-matched current Word builder in app.py in an isolated offline runner, the live Year 6 Word compactor and LibreOffice conversion to PDF. Reports one-page A4 status, Word and PDF creation, potential PDF text-extraction loss and errors for each of 800 Lessons. The successful CI status means the audit ran, **not** that every RPH is one page or READY.

**Boundaries:** Year 5 source is DRAF and remains disabled for production. Does not exercise native ReportLab PDF output, Telegram delivery, authorise book/audio use, access DB or change quotas. No curriculum originals are modified.

CI: `.github/workflows/english-800-full-a4-verification.yml`; script: `tools/verify_english_800_word_a4.py`.

## Second-pass targeted diagnostic

The first full pass found Y2 five two-page Word files (L2,3,12,13,14), and Y5 DRAF three two-page Word files (L90,110,136), plus nine Y5 teacher-selected lessons absent from the fixed-code adapter by design. A second offline pass applies the proven 8pt compactor **only to those eight overflow samples** and creates an **offline, DRAF-only preview** from the original Year 5 teacher-choice source files. These changes do not activate teacher-choice lessons or apply an unapproved change to production Word generation. Exact lesson text is compared before/after compaction.
