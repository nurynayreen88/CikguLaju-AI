"""Read-only, fail-closed approved RPH lookup for web staging.

The database schema and approval rules MUST be configured after auditing the
real database. Never treat rpt_entries.verified alone as approval.
"""
from dataclasses import dataclass
from pathlib import Path
import sqlite3

from web.rph_document_renderer import ApprovedRPH


@dataclass(frozen=True)
class RPHLookupConfig:
    database_path: str
    table: str
    id_column: str
    title_column: str
    content_column: str
    approval_column: str
    approval_value: str
    approval_reference_column: str


def _quote_identifier(identifier: str) -> str:
    if not identifier or not identifier.isidentifier():
        raise ValueError("Invalid database identifier")
    return '"' + identifier + '"'


def load_approved_rph(config: RPHLookupConfig, lesson_id: int) -> ApprovedRPH:
    """Read one explicitly approved standalone RPH; no writes, no fallbacks.

    Configuration is trusted server-side only and must refer to an independently
    audited approval field, not merely an RPT verification flag.
    """
    if type(lesson_id) is not int or lesson_id <= 0:
        raise ValueError("Invalid lesson ID")
    path = Path(config.database_path).resolve(strict=True)
    if not path.is_file():
        raise ValueError("Database path is not a file")
    fields = (
        config.table, config.id_column, config.title_column,
        config.content_column, config.approval_column,
        config.approval_reference_column,
    )
    table, id_col, title_col, body_col, approval_col, reference_col = map(
        _quote_identifier, fields
    )
    query = (
        f"SELECT {id_col}, {title_col}, {body_col}, {reference_col} "
        f"FROM {table} WHERE {id_col} = ? AND {approval_col} = ? LIMIT 2"
    )
    # Immutable mode prevents SQLite sidecars and writes. Never connect to a
    # live writable production database through this staging adapter.
    uri = path.as_uri() + "?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True, timeout=3) as conn:
        rows = conn.execute(query, (lesson_id, config.approval_value)).fetchall()
    if len(rows) != 1:
        raise LookupError("Approved standalone RPH not found or ambiguous")
    rid, title, body, reference = rows[0]
    if not isinstance(title, str) or not title.strip():
        raise LookupError("Approved RPH title missing")
    if not isinstance(body, str) or not body.strip():
        raise LookupError("Approved RPH content missing")
    if not isinstance(reference, str) or not reference.strip():
        raise LookupError("Approval reference missing")
    return ApprovedRPH(rid, title, body, reference)
