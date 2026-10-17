"""Read-only page/SP evidence parser for extracted 2026 PJ RPTs.

The page numbers here are what the supplied RPT states (BT m/s / BUKU TEKS
M/S). They are not falsely labelled as an independent textbook-PDF audit.
"""
import re
import unicodedata
from pathlib import Path

ROW_RE = re.compile(r"(?<!\d)(\d{1,2})\s+Kump(?:ulan)?\s*A\s*:", re.I)
PAGE_RE = re.compile(r"(?:BT\s*m/s|BUKU\s*TEKS\s*M/S)\s*([0-9]+(?:\s*-\s*[0-9]+)?)", re.I)
SP_RE = re.compile(r"(?<!\d)(\d+\.\d+\.\d+)(?!\d)")


def _norm(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _unit_core(unit_title):
    value = str(unit_title or "").strip()
    if ":" in value:
        value = value.split(":", 1)[1]
    value = re.sub(r"^\s*unit\s*\d*\s*", "", value, flags=re.I)
    return _norm(value)


def _blocks(text):
    marks = list(ROW_RE.finditer(text))
    result = []
    for index, match in enumerate(marks):
        start = match.start()
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        block = text[start:end]
        pages = []
        for page in PAGE_RE.findall(block):
            page = re.sub(r"\s+", "", page)
            if page not in pages:
                pages.append(page)
        codes = sorted(set(SP_RE.findall(block)))
        result.append({"week": match.group(1), "text": block, "pages": pages, "sp_codes": codes})
    return result


def lookup_page_evidence(year_label, subject, unit_title, topic, root=None):
    """Look up a page only on a same-year PJ RPT block with exact unit+topic."""
    if subject != "Pendidikan Jasmani":
        return {"status": "SOURCE_TEXT_NOT_AVAILABLE", "pages": [], "rpt_sp_codes": [], "source_file": ""}
    match = re.fullmatch(r"Tahun\s+([1-6])", str(year_label or "").strip(), re.I)
    if not match:
        return {"status": "SOURCE_SCOPE_INVALID", "pages": [], "rpt_sp_codes": [], "source_file": ""}
    base = Path(root) if root else Path(__file__).resolve().parent
    filename = f"rpt_pj_tahun_{match.group(1)}_2026_extracted.txt"
    path = base / "curriculum_sources" / "pjpk" / filename
    if not path.is_file():
        return {"status": "SOURCE_TEXT_NOT_AVAILABLE", "pages": [], "rpt_sp_codes": [], "source_file": filename}
    text = path.read_text(encoding="utf-8-sig")
    topic_norm, unit_norm = _norm(topic), _unit_core(unit_title)
    if not topic_norm or not unit_norm:
        return {"status": "TOPIC_OR_UNIT_MISSING", "pages": [], "rpt_sp_codes": [], "source_file": filename}
    matches = []
    for block in _blocks(text):
        body = _norm(block["text"])
        if topic_norm in body and unit_norm in body and block["pages"]:
            matches.append(block)
    if not matches:
        return {"status": "NO_EXACT_UNIT_TOPIC_MATCH", "pages": [], "rpt_sp_codes": [], "source_file": filename}
    pages = sorted({p for block in matches for p in block["pages"]}, key=lambda x: (int(re.match(r"\d+", x).group()), x))
    codes = sorted({code for block in matches for code in block["sp_codes"]})
    status = "RPT_PAGE_REFERENCE_ONLY" if len(pages) == 1 else "RPT_MULTIPLE_PAGE_REFERENCES_REVIEW"
    return {
        "status": status, "pages": pages, "rpt_sp_codes": codes,
        "weeks": sorted({block["week"] for block in matches}, key=lambda x: int(x)),
        "source_file": filename,
    }
