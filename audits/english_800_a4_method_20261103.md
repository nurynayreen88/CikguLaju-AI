# 800 English RPH A4 full audit (3 Nov 2026)

Audit source: all 160 English Lessons for each of Years 2–6. Uses exact AST-matched current Word builder in app.py in an isolated offline runner, the live Year 6 Word compactor and LibreOffice conversion to PDF. Reports one-page A4 status, Word and PDF creation, potential PDF text-extraction loss and errors for each of 800 Lessons. The successful CI status means the audit ran, **not** that every RPH is one page or READY.

**Boundaries:** Year 5 source is DRAF and remains disabled for production. Does not exercise native ReportLab PDF output, Telegram delivery, authorise book/audio use, access DB or change quotas. No curriculum originals are modified.

CI: `.github/workflows/english-800-full-a4-verification.yml`; script: `tools/verify_english_800_word_a4.py`.
