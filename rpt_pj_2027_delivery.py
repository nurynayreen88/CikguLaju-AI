"""Read-only RPT PJ 2027 document delivery service for Telegram handlers.

Expected deployment directory: RPT_PJ_2027_DOCX/ with 48 individually
named Word files. No database mutations, no access bypass and no downloads
from untrusted user-supplied paths.
"""
from __future__ import annotations

from pathlib import Path

STATES = (
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri_Sembilan",
    "Pahang", "Perak", "Perlis", "Pulau_Pinang", "Sabah", "Sarawak",
    "Selangor", "Terengganu", "WP_Kuala_Lumpur", "WP_Labuan",
    "WP_Putrajaya",
)
YEARS = (4, 5, 6)
FILE_PATTERN = "RPT_PJ_2027_{state}_Tahun_{year}_v76_STAGING.docx"


class RPTAccessDenied(PermissionError):
    pass


class RPTDocumentUnavailable(FileNotFoundError):
    pass


def list_available(root):
    """List only known, explicitly provisioned RPT Word files."""
    root = Path(root) / "RPT_PJ_2027_DOCX"
    if root.is_symlink():
        return []
    result = []
    for state in STATES:
        for year in YEARS:
            name = FILE_PATTERN.format(state=state, year=year)
            if (root / name).is_file() and not (root / name).is_symlink():
                result.append({"negeri": state.replace("_", " "),
                               "tahun": year, "filename": name})
    return result


def resolve_rpt(root, *, negeri, tahun, authorized):
    """Validate trusted authorization before resolving a document path.

    Telegram handler must call its existing authoritative paid-access check
    before passing authorized=True. Do not trust a Telegram callback flag.
    """
    if not authorized:
        raise RPTAccessDenied("RPT memerlukan langganan atau Rakan Pembangun aktif")
    state = str(negeri).strip().replace(" ", "_")
    if state not in STATES:
        raise ValueError("Negeri tidak sah")
    if type(tahun) is int:
        year = tahun
    elif isinstance(tahun, str) and tahun in ("4", "5", "6"):
        year = int(tahun)
    else:
        raise ValueError("Tahun tidak sah")
    if year not in YEARS:
        raise ValueError("Tahun tidak tersedia")
    folder = Path(root) / "RPT_PJ_2027_DOCX"
    if folder.is_symlink():
        raise RPTDocumentUnavailable("Untrusted RPT asset directory")
    root = folder.resolve()
    name = FILE_PATTERN.format(state=state, year=year)
    path = root / name
    if not path.is_file() or path.is_symlink():
        raise RPTDocumentUnavailable(name)
    return path


def send_rpt_docx(bot, chat_id, root, *, negeri, tahun, authorized):
    """Synchronous helper; caller handles errors and Telegram UI state."""
    path = resolve_rpt(root, negeri=negeri, tahun=tahun,
                       authorized=authorized)
    with path.open("rb") as handle:
        return bot.send_document(chat_id, handle)
