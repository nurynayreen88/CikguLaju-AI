# CikguLaju Web V1 — Zero Additional Hosting Cost Plan

Status: staging design only; no production changes.

## Architecture
- Keep the existing Render service, Flask app, Telegram bot and database.
- After auditing the real app and schema, mount web routes under `/web` in the **same** Flask service; do not create a second paid Render service.
- Serve HTML/CSS as static assets or Flask templates. No new JavaScript framework, worker, Redis or paid SaaS required for MVP.
- Continue using the existing `onrender.com` URL. A custom domain is optional, not required.
- Do not duplicate lesson, RPH, payment or entitlement tables.

## Cost caveats
- Target **RM0 incremental hosting cost**, not free overall: the existing Render plan continues to incur its normal charges.
- Web traffic, document generation, outbound bandwidth, storage and database limits may require an upgrade as usage grows.
- Current service is one instance with 512 MB RAM. Benchmark simultaneous Telegram + web PDF/Word generation before enabling.
- No cost or capacity guarantee until load tests and Render billing are reviewed.

## Safety and release checklist
1. Obtain actual `app.py` and schema through a reliable read-only method; GitHub fetch currently returns empty content.
2. Confirm existing authentication, quota decrement, subscriptions, document generation and Telegram webhook routes.
3. Implement authenticated web session and secure Telegram account linking; do not accept arbitrary Telegram IDs.
4. Read-only lesson catalog adapter must use existing verified lesson mappings.
5. Use the existing generator; charge only after successful output; enforce idempotency and concurrent access.
6. Test Jawi PDF, English audio/book links, free quotas, paid RPT gating, and Telegram regression.
7. Run resource tests under the current 512 MB limit and define rollback.
8. Keep web disabled until review; merge to `main` and deploy only with explicit approval.

## Current implementation
- `web_v1_preview/index.html`: nonfunctional mobile-first preview.
- `tools/run_web_v1_preview.py`: localhost-only preview runner.
- `cikgulaju_web_v1.py`: disabled-by-default, fail-closed blueprint scaffold.
- `web_v1_lesson_catalog.py`: unconfigured read-only catalog interface.
- `tests/test_*web*v1*.py`: test definitions, not yet executed.
