"""Standalone, isolated WSGI entrypoint for CikguLaju Web staging.

Start with: gunicorn web_staging_app:app
Never imports the Telegram production app or opens its database.
"""
from pathlib import Path
from flask import Flask, send_file
from cikgulaju_web_v1 import register_web_v1

ROOT = Path(__file__).resolve().parent


def create_app():
    app = Flask(__name__)
    register_web_v1(app, enabled=True, catalog_only=True)

    @app.get("/")
    def home():
        response = send_file(ROOT / "web_v1_static_preview" / "index.html")
        response.headers["Cache-Control"] = "no-store"
        return response

    return app


app = create_app()
