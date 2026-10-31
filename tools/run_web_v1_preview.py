"""Run the isolated Web V1 preview without importing production app.py.

Local-only command:
    python tools/run_web_v1_preview.py

The preview contains no authentication, database access or generation endpoints.
Do not expose this development server to the public internet.
"""
from pathlib import Path
import sys

from flask import Flask, send_file

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "web_v1_preview" / "index.html"
app = Flask(__name__)


@app.get("/")
def preview():
    return send_file(PREVIEW, mimetype="text/html", conditional=True)


@app.get("/health")
def health():
    return {"status": "preview-only", "database_connected": False, "generation_enabled": False}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
