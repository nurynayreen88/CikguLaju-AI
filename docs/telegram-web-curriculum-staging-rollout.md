# Telegram–Web curriculum API: controlled staging integration

The isolated Web service currently returns HTTP 503 because its authoritative
curriculum source is not configured and the Telegram runtime does not yet serve
the read-only curriculum routes. This document does **not** authorize a
production rollout.

## Staging integration

1. Keep production Telegram running with its current `gunicorn app:app`.
2. The optional `tools/run_telegram_curriculum_wsgi.py` imports the Telegram
   app only in the Telegram runtime, verifies that the v26.00 master DB is
   active, and registers the read-only blueprint when enabled.
3. In a separate, explicitly approved staging Telegram runtime, configure
   `CIKGULAJU_CURRICULUM_API_ENABLED=1` and a newly generated, secret
   `CIKGULAJU_AUTHORITATIVE_API_TOKEN` (at least 32 characters).
   Use `gunicorn tools.run_telegram_curriculum_wsgi:app` only for that runtime.
   **Do not reuse Telegram bot tokens or put secrets in GitHub.**
4. Verify unauthorized requests return 401 and authorized requests for
   `/internal/curriculum/v1/subjects?year=2` return
   `{"source":"telegram-runtime-v1","items":[...]}` using actual v26.00
   data. Check units and lessons for the same subject and unit. Check that
   materials fail closed with 503 until approval/delivery mapping exists.
5. Configure the isolated Web staging service with
   `CIKGULAJU_AUTHORITATIVE_API_URL` set to the verified **HTTPS** Telegram
   staging origin and the same dedicated API token. Verify the browser
   dropdowns only after authenticated Telegram login.
6. Audit logs, response counts, and source parity before considering a
   production rollout. Do not enable generation, charging, or material
   download from these read-only endpoints.

## Release gates

- Confirm that the Telegram runtime truly activated v26.00 and no fallback.
- Confirm that both services read the **same runtime database**, not copies.
- Confirm the subject code mapping and Year 1 KP2027 coverage.
- Confirm PJPK component separation (PJ vs PK) before exposing it.
- Confirm full lesson counts and material approvals before declaring complete.
- Confirm bot delivery and trial ledger unaffected.

All new modules live on `staging/cikgulaju-web-v1`. No production DB
migration, overwrite, or Render configuration change is included.
