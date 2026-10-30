"""Safe, pinned v76 RPT PJ 2027 provisioning and smoke tests.

Usage: python scripts/provision_rpt_pj_2027_v76.py ARCHIVE.zip NEW_DATA_DIRECTORY
Requires the exact 48-file archive audited on 2026-10-30.
Does not modify bot code, database or existing Word files.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rpt_pj_2027_delivery import STATES, YEARS, list_available, resolve_rpt
from scripts.install_rpt_pj_2027_assets import install
from scripts.verify_rpt_pj_2027_v76 import verify

EXPECTED_ARCHIVE_SHA256 = "69a24f9727ff979fa576627ab8f369e6f691871c8bf411c9ca5d3ea683cfd1f1"


def provision(archive, data_root):
    archive = Path(archive)
    data_root = Path(data_root)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Archive SHA-256 differs from reviewed v76 release")
    problems = verify(archive)
    if problems:
        raise ValueError("v76 archive validation failed: " + "; ".join(problems[:5]))
    if data_root.exists():
        raise FileExistsError("Use a NEW data directory; existing directory not modified")
    # Existing installer creates the target folder only after all archive checks.
    count = install(archive, data_root)
    try:
        actual = list_available(data_root)
        if count != 48 or len(actual) != 48:
            raise RuntimeError("Post-install RPT catalogue incomplete")
        for state in STATES:
            for year in YEARS:
                path = resolve_rpt(data_root, negeri=state, tahun=year, authorized=True)
                if not path.is_file():
                    raise RuntimeError("Missing RPT: " + state + "/" + str(year))
    except Exception:
        # A failed post-install smoke test must not leave a partial release.
        # This destination was required not to exist before installation.
        import shutil
        shutil.rmtree(data_root)
        raise
    return {"installed": count, "states": len(STATES), "years": list(YEARS),
            "archive_sha256": digest, "data_root": str(data_root)}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: provision_rpt_pj_2027_v76.py ARCHIVE.zip NEW_DATA_DIRECTORY")
    print(json.dumps(provision(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))
