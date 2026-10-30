"""Read-only release preflight for CikguLaju RPT PJ 2027.

Usage: python scripts/preflight_rpt_pj_2027.py ZIP_PATH DATA_ROOT
Prints a machine-readable release gate report. No deployment or DB changes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rpt_pj_2027_delivery import STATES, YEARS, list_available, resolve_rpt
from scripts.provision_rpt_pj_2027_v76 import EXPECTED_ARCHIVE_SHA256
from scripts.verify_rpt_pj_2027_v76 import verify


def preflight(archive, data_root):
    archive, data_root = Path(archive), Path(data_root)
    report = {"archive_verified": False, "assets_installed": False,
              "telegram_registered": False, "production_deployed": False,
              "release_ready": False, "problems": []}
    if not archive.is_file():
        report["problems"].append("Approved v76 archive unavailable")
    else:
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        report["archive_sha256"] = digest
        if digest != EXPECTED_ARCHIVE_SHA256:
            report["problems"].append("Approved archive SHA-256 mismatch")
        else:
            try:
                failures = verify(archive)
                report["problems"].extend(failures)
                report["archive_verified"] = not failures
            except Exception as exc:
                report["problems"].append("Archive verification error: " + str(exc))
    try:
        catalogue = list_available(data_root)
        expected = {(state, year) for state in STATES for year in YEARS}
        found = {(item["negeri"].replace(" ", "_"), item["tahun"]) for item in catalogue}
        report["installed_count"] = len(found)
        if found == expected:
            report["assets_installed"] = True
        else:
            report["problems"].append(f"Installed assets incomplete: {len(found)}/48")
    except Exception as exc:
        report["problems"].append("Installed assets check failed: " + str(exc))
    # A local preflight cannot attest to a registered production callback or
    # deployed service. These flags intentionally stay false.
    if not report["telegram_registered"]:
        report["problems"].append("Telegram app.py integration not verified")
    if not report["production_deployed"]:
        report["problems"].append("Render deployment not verified")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: preflight_rpt_pj_2027.py ZIP_PATH DATA_ROOT")
    result = preflight(sys.argv[1], sys.argv[2])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(not result["release_ready"])
