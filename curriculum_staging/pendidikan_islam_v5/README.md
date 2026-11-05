# Pendidikan Islam 2027 V5 — staging integration (5 Nov 2026)

**This folder is deliberately isolated and NOT wired into app.py, Telegram, Web, database, subscriptions, or production.**

## Verified local integration artifacts in ChatGPT Library

Library folder: `/CikguLaju/Pendidikan_Islam_2027_STAGING/`

1. `CIKGULAJU_PI_2027_T2_T6_RPH_RPT_TASMI_V5_INTEGRASI_STAGING_20261105.zip`
   - SHA256: `36e68d13d84f0f8edd2622b6414362020e9a3a0498d6b195c5f193a2a2132b3a`
   - 696 distinct RPH DOCX (byte-identical to V3), five Word RPTs, five RPT PDFs, eight optional tasmi PDF guides; ZIP CRC, all 696 SHA verified.
2. `CIKGULAJU_PI_2027_RPH_696_PDF_PRATONTON_V5_STAGING_20261105.zip`
   - SHA256: `d491d58aa846ad3ec9f199491ce5b8c63501518ee9774096eb3eed8d4bcccddf`
   - 696 one-page A4 PDF previews; 104 corrected V3 outputs with verified audit SHA and 592 prior PDFs whose source Word files are unchanged; all visible text blocks within page bounds.
3. The tasmi' guide is a **teacher-choice supplement**, not a rewrite of official SP or RPT. Exclusions are linked to T2-L035, T3-L145, T5-L141, T6-L014/L018/L026/L137/L141. Three other optional surah gaps also remain documented in the guide.

## Code here

- `bundle_reader.py` reads a local integration ZIP, only with `staging=True`. It validates 696 records, eight optional guides, SHA-256 when reading Word, and blocks exposure as LIVE by default.
- `preview_reader.py` reads the separate 696-preview PDF ZIP, with matching fail-closed behavior.
- Unit tests use synthetic 696 files to check staging guard, integrity errors, duplicate/missing, plus optional real-bundle integration when `PI_V5_ARCHIVE` and `PI_V5_PREVIEW_ARCHIVE` point to local ZIPs.
- `.github/workflows/pi-v5-staging-readers.yml` runs synthetic tests on the PR. CI **does not** have the private ZIPs; CI green is NOT full runtime verification.
- Local real-artifact test: **9/9 tests pass** with both ZIPs mounted; 696 real PDF verified for A4/single-page/no overflow; bytes in each RPH match V3 QA matrix.

## Release gate / blockers (NO-GO as of 2026-11-05)

- Source gaps and surah coverage supplements are documented, but **not approved as official curricular changes**.
- All 696 RPH have structural auditing, not full one-by-one semantic certification against the textbook/DSKP by a subject expert.
- Actual 86+ MB binary distribution is in Library, not GitHub/Render; current Telegram path does not read these ZIPs. It cannot deliver the files until an approved deployment transport is established and tested on staging.
- Web and Telegram selection/preview/download flows, access control, and user-data regressions not yet exercised with real deployed staging runtime.
- No merges to `main`; no changes to live `app.py`, DB, prices, menus, or subject data.

**Do NOT label READY or merge/deploy this PR. This is only a safe, testable step toward release.**
