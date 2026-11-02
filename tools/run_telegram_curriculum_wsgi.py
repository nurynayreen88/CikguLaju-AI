"""Staging-only WSGI entrypoint for the Telegram curriculum read-only API.

Never select this entrypoint for production. Refuse startup before importing
app.py unless an isolated staging runtime has explicitly opted in.
Production continues using gunicorn app:app.
"""
import os

# Check BEFORE importing Telegram app.py: its module-level startup may have
# side effects, so a misconfigured runtime must fail without importing it.
if os.environ.get("CIKGULAJU_ENV") != "staging":
    raise RuntimeError("Telegram curriculum WSGI requires isolated staging environment")
if os.environ.get("CIKGULAJU_CURRICULUM_API_ENABLED") != "1":
    raise RuntimeError("Telegram curriculum API must be explicitly enabled")
if len(os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")) < 32:
    raise RuntimeError("Dedicated curriculum API token must be at least 32 characters")

# This service must never have Telegram bot credentials or a webhook target.
# Refuse to import the large runtime if a production bot environment was copied.
if os.environ.get("BOT_TOKEN") or os.environ.get("WEBHOOK_URL"):
    raise RuntimeError("Isolated curriculum staging must not have Telegram bot credentials or webhook URL")

import app as telegram_runtime
app = telegram_runtime.app
from web.telegram_curriculum_api import create_curriculum_blueprint


def _active_primary_db():
    # Fail closed if Telegram has fallen back from its audited v26.00 master.
    if not getattr(telegram_runtime, 'CIKGULAJU_DB_V2600_ACTIVE', False):
        return None
    return getattr(telegram_runtime, 'DB_PATH', None)


app.register_blueprint(create_curriculum_blueprint(_active_primary_db))
