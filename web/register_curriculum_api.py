"""Optional read-only curriculum API registration for the existing Telegram Flask app.

Integration is deliberately opt-in: call register_if_enabled(app, lambda: DB_PATH)
from the Telegram process *after* app and DB_PATH are initialized. This module
does not import app.py, create a database, or touch webhook routes.
"""
import os


def register_if_enabled(flask_app, database_path_provider):
    """Return True only when the explicitly enabled API is registered."""
    if os.environ.get("CIKGULAJU_CURRICULUM_API_ENABLED") != "1":
        return False
    if len(os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")) < 32:
        raise RuntimeError("Curriculum API requires a dedicated 32+ character token")
    if not callable(database_path_provider):
        raise TypeError("Active Telegram database provider must be callable")
    from web.telegram_curriculum_api import create_curriculum_blueprint
    flask_app.register_blueprint(create_curriculum_blueprint(database_path_provider))
    return True
