# Telegram → Web RPH parity audit (2026-11-02)

## Verified production paths
- Production `english_y2_standalone_render.py` applies existing Year 2 standalone Markdown to Telegram RPH rows, with fallback to existing generator. It does **not** require a `READY FOR RELEASE` Markdown marker to select source.
- Production `tests/test_rph_trial_delivery_20261027.py` confirms the Telegram `send_document` wrapper consumes a free trial only after a successful RPH delivery acknowledgement, and only once.
- Production `requirements.txt` includes `python-docx==1.1.2` and `reportlab==4.2.5`.

## Current Web mismatch
- Web `web/english_release_gate.py` requires an exact `**QA status:** READY FOR RELEASE` marker, unlike Telegram's existing lesson selection.
- Web `/api/web/english/rph` renders Markdown through a separate renderer, not the Telegram row renderer; it does not implement the production trial/entitlement debit transaction.
- Web Render build command currently installs Flask/Gunicorn only; document render libraries are not guaranteed available.
- Supabase `cikgulaju_materials` and `rph_generation_history` tables had no rows in read-only checks; do not infer downloadable stored files.

## Safe parity implementation contract
1. Extract or reuse the **actual production RPH generation + document renderer** in a shared callable module without changing Telegram behavior.
2. Web calls that shared module using the authenticated Telegram user ID and validated Year/Subject/Lesson selection, never browser-supplied entitlements.
3. Implement an atomic, idempotent, server-side quota/entitlement check and debit following successful Web document delivery; test retries and failures. No direct reuse of Telegram `send_document` for HTTP downloads.
4. Use the same source and fallback rules as Telegram; avoid inventing an extra QA requirement solely for Web, but do not expose material not reachable in Telegram.
5. Install required document libraries in Web and test real Word/PDF bytes, headers, one-page rendering, and cross-account authorization.
6. Only enable public Web download after parity and quota tests pass. Preserve `main`, existing DB, and all RPH files.

**Current status: NOT IMPLEMENTED.** This audit is a plan and a source-backed gap record, not an enabled download feature.
