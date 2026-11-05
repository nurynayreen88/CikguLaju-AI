# CikguLaju Web — production integration record (5 Nov 2026)

This is the **dedicated Web service**, not the previous static staging site:
- Public Render service: https://cikgulaju-web.onrender.com
- Render service ID: `srv-dbm5go8u01pc738f40cg`
- Source branch: `production/cikgulaju-web-20261105`, based on `main` at `1deb23f`
- WSGI: `tools.run_web_production:app`
- Python dependency set: Flask 3.1.3 / Gunicorn 23.0.0
- No mutations to Telegram production service, Supabase tables, payments, referrals, quotas, or user history.

## Server-side configuration required

Some values are set as non-secret Render configuration: `CIKGULAJU_WEB_CATALOG_MODE=telegram-api`, `CIKGULAJU_AUTHORITATIVE_API_URL=https://cikgulaju-ai.onrender.com`, `SUPABASE_URL`, `CIKGULAJU_WEB_ENVIRONMENT=production`. A unique strong Web session signing key has also been installed into the service's environment (not committed).

Copy the following existing configuration **inside the Render dashboard, not in code or a chat message**, from the owner-managed services and bot settings:
- `CIKGULAJU_WEB_BOT_TOKEN` — the authorized Telegram login bot token.
- `CIKGULAJU_WEB_BOT_USERNAME` — its public bot username.
- `SUPABASE_SECRET_KEY` — server-side key for existing account lookup (never expose to browser).
- `CIKGULAJU_AUTHORITATIVE_API_TOKEN` — exact strong bearer key already configured in the Telegram curriculum service.
- Configure the bot's Telegram Login domain with BotFather for `cikgulaju-web.onrender.com`.

The Web is not authenticated or product-ready until these are configured and actual signed-in smoke tests pass. `/healthz` proves liveness only; `/readyz` checks account configuration and actual authorized curriculum source reachability. Never report `/healthz=200` as RPH delivery approval.

## RPH sources now present on the Web's main-based branch

The files listed here are in the repository snapshot; **presence is not approval**:

| Subject | Existing source | Release limitation |
| --- | --- | --- |
| English Years 2–6 | Standalone lesson-specific Markdown and official SOW index | Some lessons still have audio, layout or final QA pending. Match exact Lesson identity. |
| Pendidikan Moral | Standalone source and DSKP crosswalk | DRAF, not universally FINAL READY. |
| PJPK | Standalone source by PJ/PK and year | DRAF and component/individual source checks outstanding. |
| PSV Years 2–6 | 210 source Markdown RPH in `rph_standalone/psv/` | DRAF; the verified release bridge requires individual approval and signed manifest. |
| Pendidikan Islam Years 2–6 | 690 source texts + 6 deliberately held entries in `rph_standalone/pendidikan_islam_draf_2027/` | None approved; six held must remain withheld. Jawi and page references require source review. |
| Matematik Years 2–6 | An external v41 archive adapter with exact checksum/585 entries | The archive is not shipped or approved for Web production. Do not silently use a stale DB template. |
| Bahasa Melayu | Telegram DB and separate review work | No verified per-Lesson standalone Web RPH pipeline in this branch. |
| Sains | Telegram curriculum/master DB | No verified per-PdP standalone Web RPH pipeline in this branch. |

Year 1 uses separately evolving KP2027 content and must not be silently mapped to older Year 2–6 sources.

## Production release sequence

1. Set the four missing environment variables within Render and Telegram Login domain; keep secrets out of the repository.
2. Confirm `/readyz` returns 200, then use a real signed-in teacher account to test catalog and RPH routes.
3. Validate paid Rakan Pembangun, active/expired subscription, anonymous and free-trial behavior; do not debit or create user records on preview.
4. Validate exact Year/Subject/Unit/Lesson binding for representative approved records, including docx and print-to-PDF A4/Jawi where applicable.
5. Publish only verified source-backed RPH; do not promote draft content or infer RPH approval from RPT availability.
6. Expand native Telegram RPH renderer via a separate, regression-tested and read-only service adapter for BM/Maths/Sains/PI when approved content is available.
7. Disable the old staging URL only after the production Web is independently verified. Do not repoint Telegram production blindly.

## Verified GitHub CI

- Web production source and authorization: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42009542548
- Web staging one-click preview and saved classes: PR #323 and PR #324 (both merged to original Web staging branch).

**Never label the site fully FINAL READY solely because Render reports LIVE.**
