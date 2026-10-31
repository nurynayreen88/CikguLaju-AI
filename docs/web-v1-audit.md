# CikguLaju Web V1 — Audit and Safe Integration Plan

Status: staging only. No production deployment or database migration authorized.

## Verified on main (2026-11-01)
- Private repository: nurynayreen88/CikguLaju-AI
- Procfile: `web: gunicorn app:app`
- requirements.txt includes Flask==3.1.0, gunicorn==23.0.0, python-docx==1.1.2 and reportlab==4.2.5.
- GitHub file fetch returned empty text for `app.py` (blob SHA 343af186f9ce97a4240e3afe6a0f3bdd1a93f91f). **Do not assume the runtime source is empty**; verify repository tree, file size, deployment source and commit before editing.
- `render.yaml`, `README.md` and `bot.py` were not found at repository root.
- No database credentials or schema have been inspected.

## Release gates (all required)
1. Confirm deployed Render service points to this repository and correct branch/commit; verify the actual Flask entrypoint.
2. Identify database engine, backup strategy, read-only schema inspection, and user/lesson/RPH/entitlement relationships.
3. Extract or wrap existing RPH generation into shared service only after tests prove Telegram output is unchanged.
4. Build web under separate routes (e.g. `/web`) and keep it disabled by default via feature flag.
5. Implement server-side authentication and Telegram account linking; never trust client-supplied Telegram IDs.
6. Share entitlement and quota accounting transactionally across web and Telegram; charge only after successful generation, with idempotency keys.
7. Verify document download authorization, path traversal protection, request size limits, CSRF, session cookies, and rate limiting.
8. Test simultaneous web/Telegram generation, rollback and backup restore on staging.
9. Deploy only after explicit approval; no auto-merge to main.

## Proposed MVP
- Mobile-first Bootstrap interface: year -> subject -> unit/lesson -> preview -> generate -> download.
- Reuse approved lesson/RPH/Student Book/Workbook/audio mappings; no content regeneration.
- Preserve existing Telegram user journeys and menu.
- Add RPH Hari Ini, RPH Minggu Ini, RPT 2027 only after basic generation and account linking pass tests.

## Next inspection
- Obtain reliable repository tree / file sizes and inspect actual application entrypoint.
- Compare deployed Render configuration with GitHub; do not expose secrets.
- Write an API inventory and data-flow map before implementation.
