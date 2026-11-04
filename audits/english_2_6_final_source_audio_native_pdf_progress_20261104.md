# CikguLaju English Year 2–6 — evidence toward FINAL READY (4 Nov 2026)

This file extends, but **does not replace**, `audits/english_2_6_800_lesson_technical_readiness_20261104.md`.

## Complete native PDF structure audit

The test tool `tools/audit_english_native_pdf_core_20261104.py --year N --all` extracts the actual RPH PDF table function from `app.py` using Python 3.12 AST and compiles/runs it *without importing the live Flask/Telegram application*. It supplies the 800 source-to-document rows already verified by the existing Year2–6 pipeline (160 per year), while isolating display helpers and user/Telegram state. The function uses ReportLab's native PDF layout; this is **not** a Word-to-PDF conversion.

| English Year | Built successfully | Exactly one A4 page |
|---|---:|---:|
| 2 | 160/160 | 160/160 |
| 3 | 160/160 | 160/160 |
| 4 | 160/160 | 160/160 |
| 5 | 160/160 | 160/160 |
| 6 | 160/160 | 160/160 |
| **Total** | **800/800** | **800/800** |

GitHub Actions workflow: `.github/workflows/english-native-pdf-audio-evidence-20261104.yml`. Its five matrix jobs produce detailed per-Lesson JSON logs and fail on layout errors, page overflow, source-standard mismatch, or loss of explicit DRAF labels. In isolated tests there were **no errors or overflow**. No production files, database, entitlement, source RPH or Telegram chats are modified.

**Limitations:** The core's supporting display helpers are controlled test stubs, rather than every dynamically patched production helper; no actual Telegram user download, native PDF delivery via bot, or file access entitlement has been observed. A passing source-content render cannot prove independently that the printed SB/TB/WB page or audio track is correct.

## Year 4 Lesson 30 source conflict — independently inspected

- Original **Get Smart Plus 4 Teacher's Book p.39 (PDF page 25)**, Activity 2: **Class CD1 — Track 29**. Inspected visually against the original scanned page.
- Original KPM **Primary Year 4 SK SOW p.66**, Lesson 30 Writing 6: **CD2, Track 29**.
- Both distinct Drive MP3 files were downloaded and decoded via FFmpeg. CD1 Track 29 is **218,335 bytes**, duration **13.325938 s**, SHA-256 `7e19b89af1a1cea0d71029a0b6ab6ca3f6a7aed5962258d432649aeca4e5b226`; CD2 Track 29 is **245,857 bytes**, duration **15.046063 s**, SHA-256 `bd1478b3d90f055a4ad6d9f1a3ebefbd303e70cd6479597106fddebc5a06bd8e`. The two files are **not byte-identical**. Correct spoken content and Telegram media mapping are **not confirmed**.
- Exact source locations, Google Drive audio file IDs and verification gates are preserved in `audits/english_y4_l030_audio_source_evidence_20261104.json`.
- **Release status remains DRAF**; printed Teacher's Book is the preferred *activity instruction* but that does not prove the corresponding playable file matches the written dialogue.

## Status: no blanket FINAL READY

Earlier technical audit: **766** fixed-SOW document rows matched, **33** SOW teacher-choice lessons are clearly labelled CikguLaju suggestions, and **1** Lesson 30 audio conflict requires direct listening. All **800 native ReportLab PDF core builds now produce one-page A4**, but source and final-user QA remain separate.

Remaining FINAL gates:

1. Compare actual printed Student's Book, Teacher's Book and Workbook activities to every outstanding Lesson reference; record per-Lesson source and checksum.
2. Listen to and verify the *content* of assigned audio tracks against the actual textbook task, and verify bot's delivered Drive file identity. **Do not infer from track number alone.**
3. Test Word and native PDF delivery through a controlled authenticated teacher Telegram account. Document the downloaded files, one-page output, and quota/entitlement behaviour.
4. Confirm the 33 teacher-choice Lesson skills/standards locally without inventing a fixed SOW CS/LS, and approve classroom feasibility.
5. Only then mark the applicable Lesson **FINAL READY**, retaining a reproducible evidence trail and without overwriting existing user DB or production service settings.
