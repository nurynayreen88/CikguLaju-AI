"""Optional production-compatible WSGI entrypoint for reviewed deployment.

Not active until the Render start command is explicitly changed from
'gunicorn app:app' to 'gunicorn tools.run_telegram_with_curriculum_api:app'.
No database copies, migrations, webhook registration, or bot token changes.
"""
import app as telegram_runtime
from web.register_curriculum_api import register_if_enabled

from web.english_y2_verified_workbook_runtime import install as install_english_y2_workbook

# Preserve all existing handlers; add only verified Year 2 Workbook availability.
ENGLISH_Y2_WORKBOOK_BRIDGE_ACTIVE = install_english_y2_workbook(telegram_runtime)

app = telegram_runtime.app


def active_master_database():
    if not getattr(telegram_runtime, "CIKGULAJU_DB_V2600_ACTIVE", False):
        return None
    return getattr(telegram_runtime, "DB_PATH", None)


register_if_enabled(app, active_master_database)
