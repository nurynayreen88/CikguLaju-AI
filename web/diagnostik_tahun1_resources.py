"""Optional Year 1 diagnostic materials catalogue for CikguLaju Web.

This is a separate resource catalogue, NOT a curriculum lesson or RPH generator.
Fail closed by default: Web must supply its real authenticated/entitlement checker
and opt in with CIKGULAJU_T1_DIAGNOSTIK_ENABLED=1. No billing/credit mutation.
Files must be mounted at an administrator-configured path and match the
reviewed manifest exactly before download links appear.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from flask import Blueprint, abort, jsonify, send_file, url_for

CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "materials" / "diagnostik_tahun1" / "catalog.json"
)
DEFAULT_ASSETS = CATALOG_PATH.parent / "assets"
MAX_SIZE = 20 * 1024 * 1024


def _manifest():
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if data.get("package_id") != "CIKGULAJU-AI-T1-DIAG-2027":
        raise ValueError("Unexpected diagnostic catalogue identity")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Invalid diagnostic material listing")
    return data


def _asset_root():
    location = os.getenv("CIKGULAJU_T1_DIAGNOSTIK_ASSETS_DIR", "")
    return Path(location).resolve() if location else DEFAULT_ASSETS.resolve()


def _verified_path(item, root):
    """Only serve known single-file manifest entries with matching SHA-256."""
    name = item.get("file")
    expected = item.get("sha256", "")
    expected_size = item.get("size_bytes")
    if (
        not isinstance(name, str)
        or not name
        or name in (".", "..")
        or "/" in name
        or "\\" in name
        or not isinstance(expected, str)
        or len(expected) != 64
        or any(ch not in "0123456789abcdef" for ch in expected)
        or not isinstance(expected_size, int)
        or not 0 < expected_size <= MAX_SIZE
    ):
        return None
    candidate = root / name
    try:
        # No symlink escapes and no unknown files outside the manifest.
        if candidate.resolve().parent != root.resolve():
            return None
        if not candidate.is_file() or candidate.stat().st_size != expected_size:
            return None
        with candidate.open("rb") as fh:
            digest = hashlib.file_digest(fh, "sha256").hexdigest()
        if digest != expected:
            return None
    except OSError:
        return None
    return candidate


def catalogue():
    """Read-only resource list with honest per-file availability."""
    data = _manifest()
    root = _asset_root()
    result = []
    seen = set()
    for item in data["items"]:
        key = item.get("id")
        if (
            not isinstance(key, str)
            or not key.isascii()
            or not key.replace("_", "").isalnum()
            or key in seen
        ):
            raise ValueError("Invalid or duplicate diagnostic material id")
        seen.add(key)
        ready = _verified_path(item, root) is not None
        result.append({
            "id": key,
            "label": str(item["label"]),
            "file_type": str(item["mime"]),
            "status": "ready" if ready else "akan_datang",
            "pages": item.get("pages"),
        })
    return {
        "title": data["label"],
        "year": 1,
        "edition": 2027,
        "notice": data["notice"],
        "items": result,
    }


def create_blueprint(access_checker=None):
    """Mount explicitly after existing Web login + entitlement validation.

    access_checker: a callable returning true for a Web user allowed to access
    teaching resources. Do not pass an unconditional predicate in production.
    """
    bp = Blueprint("cikgulaju_t1_diagnostik", __name__)

    @bp.before_request
    def guarded():
        if os.getenv("CIKGULAJU_T1_DIAGNOSTIK_ENABLED") != "1":
            abort(404)
        if not callable(access_checker):
            abort(403)
        try:
            allowed = bool(access_checker())
        except Exception:
            allowed = False
        if not allowed:
            abort(403)

    @bp.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["Vary"] = "Cookie, Authorization"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @bp.get("/bahan/diagnostik/tahun-1")
    def list_tahun1():
        payload = catalogue()
        for item in payload["items"]:
            if item["status"] == "ready":
                item["download_url"] = url_for(
                    "cikgulaju_t1_diagnostik.download_tahun1",
                    item_id=item["id"],
                )
        return jsonify(payload)

    @bp.get("/bahan/diagnostik/tahun-1/download/<item_id>")
    def download_tahun1(item_id):
        data = _manifest()
        item = next((x for x in data["items"] if x["id"] == item_id), None)
        if item is None:
            abort(404)
        resource = _verified_path(item, _asset_root())
        if resource is None:
            abort(404)
        return send_file(
            resource,
            mimetype=item["mime"],
            as_attachment=True,
            download_name=item["file"],
            max_age=0,
            conditional=False,
        )

    return bp
