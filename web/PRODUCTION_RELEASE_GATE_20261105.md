# CikguLaju Web — Production release gate (5 Nov 2026)

This document is an explicit release gate, not a launch announcement. The Web remains on `staging/cikgulaju-web-v1` and its current Render service is not the production Web.

## Verified implementation
- The live curriculum catalog is retrieved from the existing Telegram production app through its read-only, bearer-protected `/internal/curriculum/v1/*` API. The Web is configured in `telegram-api` mode; no automatic database snapshot fallback is allowed. The runtime keeps the v26.00 master untouched.
- GitHub Actions run 41980998526 confirmed the live catalog connection and HTTP 401 on anonymous Web RPH, Word, RPT and curriculum routes.
- English Year 2–6 standalone source files are present, including the 320 existing Year 4–5 files added without overwriting Year 3.
- Exact Year/Subject/Unit/Lesson token is checked at the backend before a document can be served.
- Paid session lookup reads the existing Supabase account source. RPH trial quotas are **not** debited by Web; free trial generation remains in Telegram.
- Web has class, date and time inputs; these are checked against the selected source and included in RPH preview, Word and browser print.
- Local source tests and regression tests pass. These tests do not prove real teacher acceptance or full Telegram document layout parity.

## Explicit blockers to public production release
1. **All-subject RPH parity**: BM, Matematik, Sains, Pendidikan Islam and PSV have no verified Web RPH document pipeline. The v26.00 generic `rph_templates` and empty `rph_cache` cannot stand in for complete approved Lesson plans. The remaining subjects must use approved lesson-specific RPH sources or a safely extracted Telegram renderer.
2. **Content release status**: some English Year 5, PJPK and Pendidikan Moral standalone plans are still DRAF or awaiting source/visual/teacher QA; do not represent them as final approved Web documents.
3. **Full document parity**: A4 Word and PDF layout, Jawi shaping, SK/SP, textbook references, page count and print fidelity must be checked on the actual generated files across supported subjects.
4. **Account/entitlements**: perform actual signed-in tests with approved Rakan Pembangun, active subscriber, expired subscriber, and unregistered and free-trial accounts. No test bypass or quota modifications.
5. **Production service and Telegram Login domain**: configure a dedicated, properly named production Render Web service with its own server-side secrets, HTTPS and authorized Telegram Login domain; do not copy or reveal secret values in source or chat. Existing staging service URL ending in `-test` is not the release URL. Do not promote staging credentials blindly.
6. **End-to-end teacher path**: sign in → select exact Year/Subject/Unit/Lesson → choose class/date/time → preview → Word/PDF → verify content and download; repeat for each supported subject. No user-facing duplicate Year 6 shortcut or misleading “generate all” buttons.
7. **Release gate**: production Web may be announced only when the above checks have independent evidence and the service's deployed commit is confirmed LIVE.

## Non-destructive conditions
- Never reset, migrate, overwrite or silently switch the Telegram primary DB to make Web work.
- Supabase remains authoritative for user access and payments; Web must not create duplicate users, debits or payment requests.
- Changes to Telegram bot handlers, audio, production RPH and curriculum files are separate from this Web staging effort.
