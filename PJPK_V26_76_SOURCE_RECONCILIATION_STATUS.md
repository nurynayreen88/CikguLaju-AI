# PJPK v26.76 — Source reconciliation status

Status date: 17 October 2026  
Branch: `staging/pjpk-v26-18-review`  
Scope: isolated PJPK candidate database and private preview only. No production database is modified and no deployment is performed.

## What is now wired into the private preview

- Direct DSKP SP evidence is looked up by the exact tuple `(Tahun, subjek, kod SP)`. Conflicting source wording fails closed; no source text is copied across years or subjects.
- For Pendidikan Jasmani Tahun 1–6, the preview reads the committed 2026 RPT text extracts. When the unit/topic match is exact, it can recover SK wording in memory, show RPT page references and include a short RPT activity/assessment excerpt. These are explicitly labelled as RPT-source evidence; the database itself is not changed.
- The original database standards and the RPT source are compared. Differences are surfaced as warnings rather than silently overwriting the database.
- Production release gates remain unchanged. All previews are labelled as drafts, not approved production RPH.

## Latest source audit snapshot

These numbers are from the isolated candidate DB and committed evidence bundle; they are not claims that all source PDFs have been independently re-read.

| Audit item | Result |
|---|---:|
| PJPK RPT entries in candidate DB | 161 |
| Entries with both SK and SP links already in DB | 33 |
| Entries missing an SK link in DB | 116 |
| Direct DSKP SP evidence keys | 359 across all 12 year/subject combinations |
| SP links with exact direct-source wording match | 352 / 522 |
| SP links with conflicting direct-source wording | 1 / 522 |
| SP links with no direct DSKP text evidence yet | 169 / 522 |
| PJ entries with exact RPT standard extraction | 80 / 101 |
| PJ entries with RPT standard conflicts | 10 / 101 |
| PJ entries with RPT standard text not found | 11 / 101 |
| PJ entries with RPT page reference and matching SP code set | 73 / 101 |
| PJ entries with RPT page reference but SP code-set mismatch | 7 / 101 |
| PJ entries without an exact unit/topic RPT match | 9 / 101 |
| Independent textbook-page crosswalk rows currently in DB | 9 |

The private preview test covers 137 eligible draft entries. CI successfully rendered all 137 as one-page A4 PDFs (0 failures; 422,895 total PDF bytes) and uploaded the QA artifact [pjpk-private-draft-rph-pdfs-v2678](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/39001393022). The artifact includes a manifest and render-failure report. Every PDF is explicitly labelled as an unapproved draft.

## Still blocking production readiness

1. Reconcile the 169 SP links that have no direct DSKP text evidence. Do not infer wording from a different year or subject.
2. Resolve the one conflicting DSKP wording key.
3. Review the 10 PJ RPT extraction conflicts and 7 RPT-vs-DB SP code-set mismatches.
4. Resolve the 9 PJ entries without an exact unit/topic match.
5. Independently verify textbook page references against the textbook PDFs; the 73 RPT page matches are still RPT-sourced, not all independent PDF checks.
6. Recover/verify missing SK links in the database and validate the PK RPT source rows at individual-PdP level. The available PK Tahun 3 RPT crosswalk explicitly marks its merged blocks as requiring raw review; it must not be treated as individual lessons by week.

## Source access and safety

This session can read the RPT text extracts and source-evidence artifacts already committed to the repository/ChatGPT Library. The Google Drive connector is disabled by the workspace/admin in this session, and the linked original Drive PDFs require an authenticated file read; therefore the remaining original DSKP/textbook PDFs have not been independently re-read here. The source bundle preserves source file IDs where available so those exact references can be reopened when Drive access is available.

No Gemini/OpenAI generation API was used for these checks. The audit, cross-check and PDF render steps are local/offline.