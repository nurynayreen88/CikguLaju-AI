"""Read-only provenance check for Telegram/Web lesson catalog data.

A Web-only preview copy must never be represented as the live Telegram
source. This module reports configured provenance; it does not connect
production databases or modify existing data.
"""
import os
from pathlib import Path


def catalog_source_status(environ=None):
    env = os.environ if environ is None else environ
    web_path = env.get("CIKGULAJU_WEB_PREVIEW_DB", "")
    shared_path = env.get("CIKGULAJU_SHARED_CATALOG_DB", "")
    if not web_path or not shared_path:
        return {"shared_source_verified": False,
                "reason": "shared catalog database not configured"}
    try:
        web = Path(web_path).resolve(strict=True)
        shared = Path(shared_path).resolve(strict=True)
        if not web.is_file() or not shared.is_file():
            return {"shared_source_verified": False, "reason": "catalog source unavailable"}
        if not web.samefile(shared):
            return {"shared_source_verified": False, "reason": "Web catalog differs from shared catalog"}
    except (OSError, ValueError):
        return {"shared_source_verified": False, "reason": "catalog source unavailable"}
    # Same inode is only local file identity. It does NOT prove this file is
    # the authoritative live Telegram source or receives future updates.
    return {"shared_source_verified": False,
            "same_local_file": True,
            "reason": "Same local file, but authoritative live source not verified"}
