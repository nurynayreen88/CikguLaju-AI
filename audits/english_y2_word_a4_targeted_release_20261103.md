# English Tahun 2: five overflowing RPH Word — safe production patch

**Scope:** Word export after the existing RPH generator, only Year 2 English Lessons 2, 3, 12, 13, 14. Exact RPH source is **not rewritten**; the patch reuses the existing and previously deployed Year 6 Word 8pt atomic compactor.

**Evidence:** 800-source [A4 CI audit](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41644999160) generated all 160 Year 2 DOCX and converted them to one-page A4 when these five were compacted. The patch does not change Word output for other 155 Year 2 lessons, Year 3–6, subjects or worksheets; PDF-native generator, Telegram callbacks, user DB and quotas stay unchanged.

**Release boundary:** This verifies offline Word→PDF output, not a real user Telegram send or the native PDF generation. No blanket READY claim; Year 5 DRAF runtime remains disabled. `tests/test_english_y2_word_a4_runtime.py` and Year2 full A4 CI must pass before merge.
