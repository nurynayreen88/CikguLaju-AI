# Web V1: verified generator integration boundary (2026-11-01)

Source inspected: `app.py` on `main`, blob `343af186f9ce97a4240e3afe6a0f3bdd1a93f91f`.

## Existing generator, not a mock

- `_local_rph_text(ctx)` produces RPH content in the existing Telegram engine.
- `create_pdf_file(ctx, text, cid)` produces the PDF path; final override v26.26 removes RPH footers.
- `_create_rph_word(doc, section, s, ai_text, path)` builds Word content.
- `_generate_one_quick_rph_v25278(cid, entry)` is **not** an HTTP-safe adapter: it writes Telegram state, invokes `send_document`, and records usage after delivery.
- The `send_document` function is repeatedly wrapped, including usage statistics and delivery bookkeeping. **Do not call it from web requests.**
- `app.py` reconstructs a split DB at import time and defines Flask/webhook globals. **Do not import production app.py into the preview service.**

## Required production-safe extraction

1. Isolate pure RPH content and document rendering into a separate module without Telegram send, state mutation, credit debit, or app import side effects.
2. Verify an RPT/PdP ID maps to an approved standalone RPH; `rpt_entries.verified=1` alone is insufficient.
3. Add server-side session/anonymous trial quota, request validation, throttling, and idempotent debit after successful delivery. Never trust browser counters.
4. Return files through an authenticated/authorized or limited trial download endpoint, with expiry and no user-identifying path.
5. Test Word and PDF generation from a **verified** fixture and confirm both open correctly before exposing the public route.
6. Keep production Render service and `main` unchanged until isolated staging end-to-end tests pass.

## Current release status

Static Render preview is UI-only. Local Flask preview dropdowns can read an explicitly configured SQLite DB in read-only mode. `/api/generate` and `/api/materials/download/<id>` intentionally return HTTP 503. Public launch is **not ready**.
