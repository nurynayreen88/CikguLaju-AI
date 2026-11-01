# English Year 2 — exhaustive 160/160 Drive RPT vs GitHub SOW master comparison

Date: 2026-11-01. Read-only comparison.

## Sources
- Google Sheet `CIKGULAJU_RPT_2027_KALENDAR_CUTI_FINAL_VERIFIED`, tab `MASTER ENGLISH 800 LESSON 2027`, range `A2:F161` (160 Year 2 records).
- GitHub `data/english_y1y2_sow_master_320.json`, `Tahun 2` (160 records), branch `staging/english-y2-safe-supplements-20261101`.

## Method
For each Drive row, index by numeric Lesson and compare against the same-number GitHub master row: unit/tajuk (case and punctuation normalized), focus (case and punctuation normalized), and exact main SK, main SP, complementary SK and complementary SP. Parse Drive `MAIN: SK/SP | COMPLEMENTARY: SK/SP` before comparison. Also verify total count 160.

## Result
- Drive rows compared: **160**.
- GitHub Year 2 master rows available: **160**.
- Full matches on all compared fields: **160**.
- Mismatches: **0**.

## Important scope limitations
- This compares **two planning/master sources**, not every individual standalone RPH file.
- No direct inspection of live production DB, actual textbook/workbook pages, audio tracks, lesson procedure or generated Word/PDF.
- Both masters can share an upstream error; the `Language Arts 42` label at Lesson 160 still requires official SOW sequence validation.
- Drive RPT status remains draft for scheduling/state-calendar purposes. **Do not mark READY.**

No modifications to Drive Sheet, GitHub source master, original RPH, RPT, database, Telegram, web or deployment.
