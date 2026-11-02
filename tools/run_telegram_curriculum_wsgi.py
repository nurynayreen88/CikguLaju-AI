"""Optional WSGI entrypoint for staging the Telegram curriculum API.

Production's existing `gunicorn app:app` is unchanged. A future controlled
deployment may select `gunicorn tools.run_telegram_curriculum_wsgi:app`.
Never import this module from Web preview or tests: it imports Telegram app.py.
"""
import os

from app import app, DB_PATH, CIKGULAJU_DB_V2600_ACTIVE
from web.telegram_curriculum_api import create_curriculum_blueprint


def _active_primary_db():
    # Fail closed if Telegram has fallen back from its audited v26.00 master.
    if not CIKGULAJU_DB_V2600_ACTIVE:
        return None
    return DB_PATH


if os.environ.get("CIKGULAJU_CURRICULUM_API_ENABLED") == "1":
    app.register_blueprint(create_curriculum_blueprint(_active_primary_db))
