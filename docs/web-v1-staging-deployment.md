# Web V1 staging deployment checklist

Service: `cikgulaju-web-v1-api-test` (Render)
Branch: `staging/cikgulaju-web-v1`
Production Telegram: **never deploy or change**.

## Render staging configuration
- Build command: `pip install -r requirements-web-v1.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT tools.run_web_v1_preview:app`
- Leave autoDeploy OFF until explicit staging acceptance.
- Keep `CIKGULAJU_WEB_RPH_DELIVERY_EXPERIMENT` **unset** (or `0`).
- Keep `CIKGULAJU_WEB_RPH_STAGING_ENABLED` disabled until approved source, renderer parity, account entitlements and delivery accounting have been verified.

## Pre-activation gates
1. All GitHub Web V1 and RPH regression checks pass.
2. Verify Word/PDF output against Telegram's actual RPH template, including one-page A4 where applicable.
3. Verify approved lesson mapping against current curriculum database; never release pending English QA.
4. Validate 10-trial policy against the existing Supabase RPC and subscription entitlements without altering user balances.
5. Validate duplicate HTTP request handling and recovery after interrupted delivery; rendering/debit alone does not guarantee file delivery.
6. Perform end-to-end tests with mock accounts and a nonproduction database first.
7. Only then consider an explicit supervised activation.

## Known current status
The isolated pipeline and HTTP handlers are integrated behind a second disabled feature gate. Render's current build command installs only Flask and Gunicorn, so its runtime does **not** yet include the document renderer packages. The standalone renderer is **not** the production Telegram layout. Do not claim the website is ready to generate RPH.
