"""Explicitly selected PSV candidate staging WSGI entrypoint (never production).

Use only when a separate PSV staging Render service is deliberately configured
to start: gunicorn tools.psv_candidate_staging_entrypoint:app

No public DRAF preview. The PSV adapter requires a release approval file, READY
sources and CIKGULAJU_PSV_RPH_RELEASE_ENABLED=1. With any gate missing, the
existing native bot is left untouched. No change to shared production entrypoint.
"""
from tools.run_telegram_with_curriculum_api import app, telegram_runtime
from web.psv_2027_rph_release_bridge import install

PSV_RPH_CANDIDATE_ACTIVE = bool(install(telegram_runtime))
