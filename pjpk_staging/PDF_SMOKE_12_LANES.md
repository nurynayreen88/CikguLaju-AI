# PJPK PDF smoke test — 15 October 2026

The local candidate DB and preview renderer produced a real, parseable one-page PDF for each of the 12 lanes: T1–T6 × PJ/PK. Tested sample entry IDs:

| Year | PJ | PK |
|---|---:|---:|
| 1 | 2225 | 2265 |
| 2 | 2229 | 2232 |
| 3 | 2380 | 2233 |
| 4 | 2236 | 2280 |
| 5 | 2238 | 2240 |
| 6 | 2241 | 2243 |

Each PDF was checked using pdfinfo. ZIP integrity test passed. This establishes preview PDF serialization only, **not** official CikguLaju template compatibility, curriculum approval, or successful live Telegram/Render delivery. 147 REVIEW_ONLY; 13 ANCHOR_NOT_PDP; 1 SOURCE_CONFLICT_BLOCKED. Main app and master DB untouched.

To progress to a deployable private test: upload candidate DB and two renderer modules to staging without overwriting any old files; compare GitHub main app against local baseline; merge the gated integration into a staging app; verify real official-template PDF and tester-only Telegram callback; get explicit deploy approval.
