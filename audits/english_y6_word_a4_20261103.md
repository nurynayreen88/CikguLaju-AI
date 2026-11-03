# English Year 6 Word A4 — source-based 3 November 2026 QA

**Original Word snapshot parity:** `qa/english_word_builder_snapshot.py` matches the active `_create_rph_word` function in `app.py` by AST. 30 primary Y2–Y6 source-based RPH sample outputs, generated without importing `app.py` or touching Telegram/DB/credits, were converted with LibreOffice to PDF.

| Year | 1-page A4 in baseline | Samples |
|---|---:|---:|
| Year 2 | 6 | 6 |
| Year 3 | 7 | 7 |
| Year 4 | 5 | 5 |
| Year 5 (DRAF offline only) | 4 | 4 |
| Year 6 | **0** | **8** |

A controlled test then **retained all sentences** of each of eight Year 6 source plans but changed only document section margins, cell padding and table font size. **8 pt = 8/8 one-page A4**, **7.5 pt = 8/8**. The 8pt option was selected to preserve better readability.

Sources / sample outputs: [GitHub Actions run #41641121283](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41641121283) (artifact `english-y2-y6-a4-layout-audit`, 7-day retention).

The new `web/english_y6_word_a4_runtime.py` is scoped to **English Year 6, RPH, Word only** and installed via the existing WSGI entrypoint; all original text is retained. It saves atomically, preserving the previous file on errors. No change to English Year 2–5, Matematik, Telegram credits, Supabase or curriculum database.

**Release boundary:** Eight representative lessons are not 160/160 visual approval. Native PDF renderer and actual Telegram document download/playback remain untested; no blanket READY claim. Changes should be observed in one live Word export after deployment before calling Year 6 fully approved.
