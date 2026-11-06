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

## V6 restricted preview after Year → Lesson (not live)

The new `staging_gateway.py` exposes an **independent, read-only WSGI interface** for testing the exact 696 RPH candidates; it does **not** register routes into existing Telegram or Web services.

* `/api/pi/lessons?year=2`: list stages and optional tasmi guides by Lesson.
* `/api/pi/lesson?year=2&lesson=1`: metadata only, never marks final ready.
* `/api/pi/preview?year=2&lesson=1`: inline PDF preview after selection.
* `/api/pi/word?year=2&lesson=1`: draft Word download.
* `/api/pi/tasmi?year=2&lesson=35`: optional teacher-only tasmi guide.
* `/api/pi/rpt?year=2&format=pdf|docx`: draft RPT.
* `/api/pi/status`: 696 total, six held, 0 approved.

Access requires explicit `PI_V5_STAGING_GATEWAY=1`, matching `PI_V5_ARCHIVE` and `PI_V5_PREVIEW_ARCHIVE` local file paths, and a **24+ character** `PI_V5_STAGING_TOKEN`. Every non-health route requires `Authorization: Bearer <secret>`; absent/invalid auth returns 403. `TAHAN_SEMAKAN_KANDUNGAN` lessons return 423 for Word/PDF. No CORS, no cache, no default production activation, and no DB or quota changes. Both ZIP archives must be securely mounted; they do not exist on Render just because they are in ChatGPT Library.

**QA (5 Nov 2026): 25/25 local tests passed** with real ZIP files mounted, and GitHub Actions [run 41977534624](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41977534624) passed synthetic tests. They are not live Telegram message tests.

**Blocking issue confirmed:** all 696 PDF previews visibly contain `STAGING 2027` and `Bukan READY` / draft notice. The six held lessons are T2-L035, T6-L006/L014/L018/L060/L117. The content is unsuitable for public release or automatic subscription delivery until expert sign-off and revised release assets. The printed label should NOT be stripped merely to make the file appear ready.
