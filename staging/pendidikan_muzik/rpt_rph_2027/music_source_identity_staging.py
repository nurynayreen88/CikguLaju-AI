"""Staging-only read-only source-digest prototype for Music RPH.

A matching digest is NOT a release approval. Production Web/Telegram still
reject MUZIK because the subject is deliberately absent from the live source
identity router and the real renderer allowlist.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = "staging/pendidikan_muzik/rpt_rph_2027"
MAX_SOURCE_BYTES = 2_500_000


def source_paths(year, lesson, component=None):
    """Exact physical files needed for a 2027 Muzik RPH preview."""
    if type(year) is not int or type(lesson) is not int:
        return None
    if year not in range(2, 7) or lesson not in range(1, 36) or component is not None:
        return None
    prefix = f"{BASE}/year{year}"
    return (
        f"{prefix}/rph_pdp_{lesson:02d}.md",
        f"{prefix}/pdp_manifest.json",
        f"{prefix}/RPT_MUZIK_TAHUN_{year}_2027_DRAF.csv",
        f"{BASE}/SUCCESS_CRITERIA_DRAFT_20261106.json",
        f"{BASE}/KALENDAR_MINGGU_RPT_2027_INDUK_AUDIT_SNAPSHOT.json",
    )


def source_fingerprint(year, lesson, component=None, *, root=ROOT):
    """Fail closed on missing, symlinked, oversized or out-of-root sources.

    Hash construction deliberately mirrors web/rph_shared_source_identity.py:
    for each approved relative path, hash pathname + NUL + exact bytes + NUL.
    """
    paths = source_paths(year, lesson, component)
    if not paths:
        return None
    base = Path(root).resolve()
    digest = hashlib.sha256()
    for relative in paths:
        candidate = base / relative
        try:
            if candidate.is_symlink() or not candidate.is_file():
                return None
            if not candidate.resolve().is_relative_to(base):
                return None
            size = candidate.stat().st_size
            if not 0 < size <= MAX_SOURCE_BYTES:
                return None
            data = candidate.read_bytes()
        except (OSError, ValueError):
            return None
        digest.update(relative.encode("utf-8"))
        digest.update(b"\\x00")
        digest.update(data)
        digest.update(b"\\x00")
    return digest.hexdigest()


def manifest_matches_source(year, lesson, *, root=ROOT):
    """Separate integrity check, not a replacement for curriculum sign-off."""
    import csv
    import json
    paths = source_paths(year, lesson)
    if not paths:
        return False
    base = Path(root)
    try:
        manifest = json.loads((base / paths[1]).read_text(encoding="utf-8"))
        entries = manifest["pdps"]
        record = entries[lesson - 1]
        if record["pdp"] != lesson or record["pdp_id"] != f"MZ-Y{year}-{lesson:02d}":
            return False
        with (base / paths[2]).open(encoding="utf-8", newline="") as handle:
            lines = list(csv.reader(handle))
        return (len(lines) == 36 and
                lines[lesson][0] == record["pdp_id"] and
                int(lines[lesson][1]) == lesson)
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return False
