"""Build an immutable, versioned Web curriculum copy from reviewed repo parts.

Web and Telegram retain separate physical SQLite files.  Supabase remains the
single source of truth for accounts, entitlements and quota.  No production
database is opened by this module; no network request or migration is performed.
A deployment must explicitly select a checksum-bearing manifest.
"""
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]
_CHUNK = 1024 * 1024
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,150}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_RPT_FIELDS = {
    "id", "year_label", "subject", "verified", "notes", "sequence_no",
    "unit_title", "topic", "subtopic", "skill_focus",
}
# Never replicate the users, payments or subscription database as curriculum.
_FORBIDDEN_TABLES = {"cikgulaju_users", "pioneer_entitlements",
                     "subscriptions", "payments", "payment_history",
                     "telegram_users"}


class CurriculumCopyUnavailable(RuntimeError):
    """Snapshot is absent, not verified or incompatible with the Web catalog."""


def _name(value):
    if not isinstance(value, str) or not _SAFE_NAME.fullmatch(value):
        raise CurriculumCopyUnavailable("Invalid snapshot file name")
    if value in (".", "..") or ".." in value:
        raise CurriculumCopyUnavailable("Invalid snapshot file name")
    return value


def _read_manifest(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 32_768:
        raise CurriculumCopyUnavailable("Versioned manifest unavailable")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or type(data.get("size")) is not int
                or data["size"] <= 0 or not _SHA256.fullmatch(data.get("sha256", ""))):
            raise ValueError("invalid checksum manifest")
        source = _name(data.get("source"))
        if not source.endswith(".db"):
            raise ValueError("invalid DB source")
        parts = data.get("parts")
        if not isinstance(parts, list) or not 1 <= len(parts) <= 32:
            raise ValueError("invalid part list")
        seen = set()
        total = 0
        for part in parts:
            if not isinstance(part, dict):
                raise ValueError("invalid part")
            name = _name(part.get("file"))
            size = part.get("size")
            digest = part.get("sha256", "")
            if (name in seen or type(size) is not int or size <= 0
                    or not _SHA256.fullmatch(digest)):
                raise ValueError("invalid part metadata")
            seen.add(name)
            total += size
        if total != data["size"]:
            raise ValueError("part sizes disagree with total")
        return data
    except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        raise CurriculumCopyUnavailable("Invalid checksum manifest") from exc


def _verify_database(path):
    if path.open("rb").read(16) != b"SQLite format 3\x00":
        raise CurriculumCopyUnavailable("Snapshot is not SQLite")
    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True, timeout=6) as db:
            db.execute("PRAGMA query_only=ON")
            if db.execute("PRAGMA quick_check(1)").fetchone()[0] != "ok":
                raise CurriculumCopyUnavailable("SQLite integrity verification failed")
            tables = {name.lower() for (name,) in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if _FORBIDDEN_TABLES & tables:
                raise CurriculumCopyUnavailable("Account/billing table present in copy")
            if "rpt_entries" not in tables:
                raise CurriculumCopyUnavailable("Verified RPT table missing")
            columns = {item[1] for item in db.execute("PRAGMA table_info(rpt_entries)")}
            if not _REQUIRED_RPT_FIELDS <= columns:
                raise CurriculumCopyUnavailable("RPT schema incompatible with Web")
            if db.execute("SELECT COUNT(*) FROM rpt_entries WHERE verified=1").fetchone()[0] < 1:
                raise CurriculumCopyUnavailable("No verified curriculum rows")
    except sqlite3.Error as exc:
        raise CurriculumCopyUnavailable("SQLite curriculum validation failed") from exc


@lru_cache(maxsize=4)
def _materialize(manifest_name, root):
    root = Path(root).resolve()
    filename = _name(manifest_name)
    if not filename.endswith("_manifest.json"):
        raise CurriculumCopyUnavailable("Expected a versioned manifest")
    manifest = _read_manifest(root / filename)
    version = filename.removesuffix("_manifest.json")
    destination_dir = Path(tempfile.mkdtemp(prefix="cikgulaju-web-copy-"))
    temp_path = destination_dir / "unverified.db"
    destination = destination_dir / ("curriculum_" + version + ".db")
    overall = sha256()
    total = 0
    try:
        with temp_path.open("xb") as output:
            for part in manifest["parts"]:
                part_path = root / part["file"]
                if not part_path.is_file() or part_path.is_symlink():
                    raise CurriculumCopyUnavailable("Snapshot part unavailable")
                if part_path.stat().st_size != part["size"]:
                    raise CurriculumCopyUnavailable("Snapshot part size mismatch")
                digest = sha256()
                copied = 0
                with part_path.open("rb") as source:
                    while True:
                        block = source.read(_CHUNK)
                        if not block:
                            break
                        copied += len(block)
                        digest.update(block)
                        overall.update(block)
                        output.write(block)
                if copied != part["size"] or digest.hexdigest() != part["sha256"]:
                    raise CurriculumCopyUnavailable("Snapshot part checksum mismatch")
                total += copied
        if total != manifest["size"] or overall.hexdigest() != manifest["sha256"]:
            raise CurriculumCopyUnavailable("Snapshot total checksum mismatch")
        _verify_database(temp_path)
        os.chmod(temp_path, 0o400)
        temp_path.replace(destination)
        return {"path": str(destination), "version": version,
                "sha256": overall.hexdigest(), "verified": True,
                "source_kind": "versioned-web-copy"}
    except (OSError, ValueError) as exc:
        raise CurriculumCopyUnavailable("Cannot prepare verified Web snapshot") from exc
    finally:
        if temp_path.exists():
            temp_path.unlink()


def get_verified_web_copy(manifest_name, *, repo_root=None):
    """Return a private read-only path after size, SHA256 and SQLite checks.

    Every process owns its temporary artifact. The source parts and database
    remain untouched. Failed verification raises; no stale snapshot fallback.
    """
    root = ROOT if repo_root is None else Path(repo_root)
    return dict(_materialize(manifest_name, str(root.resolve())))
