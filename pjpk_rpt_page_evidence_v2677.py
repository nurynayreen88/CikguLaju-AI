"""Read-only standard/page evidence parser for extracted 2026 PJ RPTs.

The page numbers are what the supplied RPT states (BT m/s / BUKU TEKS M/S).
They are not falsely labelled as an independent textbook-PDF audit.
"""
import re
import unicodedata
from pathlib import Path

ROW_RE = re.compile(r"(?<!\d)(\d{1,2})\s+Kump(?:ulan)?\s*A\s*:", re.I)
PAGE_RE = re.compile(r"(?:BT\s*m/s|BUKU\s*TEKS\s*M/S)\s*([0-9]+(?:\s*-\s*[0-9]+)?)", re.I)
STD_RE = re.compile(r"(?<!\d)(\d+\.\d+(?:\.\d+)?)(?!\.\d)")
TRAIL_RE = re.compile(r"\s+(?:Pemerhatian|Pentaksiran|Permainan(?:\s+kecil)?|EMK\b|BT\s*m/s|BUKU\s*TEKS|AKTIVITI\s+PAK|BBB/BBM|KBAT\b|NILAI\b|Kump(?:ulan)?\s+[AB]\s*:|MINGGU\b).*$", re.I)


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


def _extract_standards(block):
    found = []
    for match in STD_RE.finditer(block):
        code = match.group(1)
        parts = [int(v) for v in code.split(".")]
        if len(parts) not in (2, 3) or parts[0] > 10 or parts[1] > 20 or (len(parts) == 3 and parts[2] > 20):
            continue
        start = match.end()
        end = len(block)
        next_match = STD_RE.search(block, start)
        if next_match:
            end = next_match.start()
        text = re.sub(r"\s+", " ", block[start:end]).strip(" \t\r\n:;.-")
        text = TRAIL_RE.sub("", " " + text).strip(" \t\r\n:;.-")
        if not text:
            continue
        kind = "SK" if len(parts) == 2 else "SP"
        row = {"standard_type": kind, "standard_code": code, "standard_text": text}
        if row not in found:
            found.append(row)
    return found


def _extract_activity_note(block):
    marker = re.search(
        r"(?:Pemerhatian\s*/\s*Pentaksiran|Pemerhatian|Pentaksiran|Aktiviti\s+PAK-21|Permainan(?:\s+kecil)?\s*:)",
        block, re.I
    )
    if not marker:
        return ""
    note = block[marker.start():]
    note = re.split(r"(?:BT\s*m/s|BUKU\s*TEKS\s*M/S)", note, maxsplit=1, flags=re.I)[0]
    note = re.sub(r"\s+", " ", note).strip(" \t\r\n:;.-")
    return note[:280]


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
        standards = _extract_standards(block)
        result.append({
            "week": match.group(1), "text": block, "pages": pages,
            "standards": standards,
            "sp_codes": sorted({x["standard_code"] for x in standards if x["standard_type"] == "SP"}),
            "activity_note": _extract_activity_note(block),
        })
    return result


def lookup_page_evidence(year_label, subject, unit_title, topic, root=None):
    """Look up same-year RPT evidence only for an exact unit+topic match."""
    if subject != "Pendidikan Jasmani":
        return {"status": "SOURCE_TEXT_NOT_AVAILABLE", "pages": [], "rpt_sp_codes": [], "rpt_standards": [], "source_file": ""}
    match = re.fullmatch(r"Tahun\s+([1-6])", str(year_label or "").strip(), re.I)
    if not match:
        return {"status": "SOURCE_SCOPE_INVALID", "pages": [], "rpt_sp_codes": [], "rpt_standards": [], "source_file": ""}
    base = Path(root) if root else Path(__file__).resolve().parent
    filename = f"rpt_pj_tahun_{match.group(1)}_2026_extracted.txt"
    path = base / "curriculum_sources" / "pjpk" / filename
    if not path.is_file():
        return {"status": "SOURCE_TEXT_NOT_AVAILABLE", "pages": [], "rpt_sp_codes": [], "rpt_standards": [], "source_file": filename}
    text = path.read_text(encoding="utf-8-sig")
    topic_norm, unit_norm = _norm(topic), _unit_core(unit_title)
    if not topic_norm or not unit_norm:
        return {"status": "TOPIC_OR_UNIT_MISSING", "pages": [], "rpt_sp_codes": [], "rpt_standards": [], "source_file": filename}
    matches = []
    for block in _blocks(text):
        body = _norm(block["text"])
        if topic_norm in body and unit_norm in body:
            matches.append(block)
    if not matches:
        return {"status": "NO_EXACT_UNIT_TOPIC_MATCH", "pages": [], "rpt_sp_codes": [], "rpt_standards": [], "source_file": filename}
    page_blocks = [block for block in matches if block["pages"]]
    pages = sorted({p for block in page_blocks for p in block["pages"]}, key=lambda x: (int(re.match(r"\d+", x).group()), x))
    activity_notes = sorted({block["activity_note"] for block in matches if block["activity_note"]})
    standard_maps = []
    for block in matches:
        standard_maps.append({
            (item["standard_type"], item["standard_code"]): item["standard_text"]
            for item in block["standards"]
        })
    distinct_maps = []
    for mapping in standard_maps:
        if mapping not in distinct_maps:
            distinct_maps.append(mapping)
    standards = []
    if distinct_maps and all(mapping == distinct_maps[0] for mapping in distinct_maps):
        standards = [
            {"standard_type": kind, "standard_code": code, "standard_text": text}
            for (kind, code), text in sorted(distinct_maps[0].items(), key=lambda x: (0 if x[0][0] == "SK" else 1, x[0][1]))
        ]
        standards_status = "RPT_STANDARDS_EXTRACTED" if standards else "RPT_STANDARDS_NOT_FOUND"
    else:
        standards_status = "RPT_STANDARD_CONFLICT_REVIEW"
    if not pages:
        page_status = "RPT_TOPIC_MATCH_NO_PAGE"
    elif len(pages) == 1:
        page_status = "RPT_PAGE_REFERENCE_ONLY"
    else:
        page_status = "RPT_MULTIPLE_PAGE_REFERENCES_REVIEW"
    sp_codes = sorted({x["standard_code"] for x in standards if x["standard_type"] == "SP"})
    return {
        "status": page_status, "pages": pages, "rpt_sp_codes": sp_codes,
        "rpt_standards": standards, "standards_status": standards_status,
        "rpt_activity_note": activity_notes[0] if len(activity_notes) == 1 else "",
        "activity_status": "RPT_ACTIVITY_EXTRACTED" if len(activity_notes) == 1 else ("RPT_ACTIVITY_CONFLICT_REVIEW" if len(activity_notes) > 1 else "RPT_ACTIVITY_NOT_FOUND"),
        "weeks": sorted({block["week"] for block in matches}, key=lambda x: int(x)),
        "source_file": filename,
    }
