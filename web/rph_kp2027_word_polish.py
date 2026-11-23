"""Conservative KP2027-inspired visual polish for verified KSSR RPH Word downloads.

Applies only to source-backed native RPH DOCX documents with recognizable
curriculum rows. Text, activities, SK/SP, teaching data, links and all other
ZIP parts remain byte-identical. Unrecognized formats are returned unchanged.
This intentionally does NOT reflow PDF or claim academic approval.
"""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZipFile

try:
    from lxml import etree
except ImportError:
    etree = None

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOC = "word/document.xml"
MAX_FILE = 15_000_000
MAX_XML = 8_000_000
ALIASES = {
    "MATH_DLP": "DLP_MATH",
    "SCIENCE_DLP": "DLP_SCIENCE",
    "MUZIK": "MUSIC",
    "PENDIDIKAN_MUZIK": "MUSIC",
    "PENGURUSAN_KEHIDUPAN_PPKI": "PPKI",
}
SENTINELS = (
    "rancangan pengajaran harian", "daily lesson plan", "رنجاڠن",
    "خطة الدرس",
)
LABELS = (
    "standard kandungan", "standard pembelajaran", "objektif", "kriteria",
    "aktiviti", "pentaksiran", "mata pelajaran", "learning standard",
    "content standard", "assessment", "success criteria", "reflection",
    "رفليكسي", "ستندرد", "اکتيۏيتي",
)

@lru_cache(maxsize=1)
def _palettes():
    try:
        path = Path(__file__).with_name("rph_login_canonical_layout_20261121.json")
        source = json.loads(path.read_text(encoding="utf-8"))
        return {
            row["subject_code"]: (
                row["tone"].lstrip("#").upper(),
                row["strong"].lstrip("#").upper(),
            )
            for row in source["subjects"]
            if re.fullmatch(r"#[0-9a-fA-F]{6}", row.get("tone", ""))
            and re.fullmatch(r"#[0-9a-fA-F]{6}", row.get("strong", ""))
        }
    except (OSError, ValueError, TypeError, KeyError):
        return {}

def _set(parent, tag, attrib):
    child = parent.find(W + tag)
    changed = False
    if child is None:
        child = etree.Element(W + tag)
        parent.append(child)
        changed = True
    for key, value in attrib.items():
        q = W + key
        if child.get(q) != value:
            child.set(q, value)
            changed = True
    return child, changed

def _text(element):
    return " ".join("".join(n.text or "" for n in element.iter(W + "t")).split())

def _style(table, tone, strong):
    rows = table.findall(W + "tr")
    if len(rows) < 2 or len(rows) > 250:
        return False
    sizes = [len(row.findall(W + "tc")) for row in rows]
    if not sizes or sizes[0] not in (2, 3) or any(size != sizes[0] for size in sizes):
        return False
    props = table.find(W + "tblPr")
    if props is None:
        return False
    changed = False
    # Preserve the native table-width unit and its exact value. In particular,
    # native English's 4-table banner has a fixed twip grid: converting tblW
    # to 100% while leaving tblGrid and tcW in dxa causes overflowing and
    # apparently overlapping boxes in some Word/PDF viewers. Cosmetic passes
    # must never introduce contradictory table geometry.
    # Only borders, soft fills and modest cell padding are changed here.
    borders, did = _set(props, "tblBorders", {})
    changed |= did
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        _, did = _set(borders, side, {"val": "single", "sz": "5", "color": "BAC7D0"})
        changed |= did
    for index, row in enumerate(rows):
        cells = row.findall(W + "tc")
        row_props = row.find(W + "trPr")
        if row_props is None:
            row_props = etree.Element(W + "trPr")
            row.insert(0, row_props)
            changed = True
        _, did = _set(row_props, "cantSplit", {})
        changed |= did
        first_label = _text(cells[0])
        label_cell = bool(first_label and len(first_label) <= 75 and len(first_label.split()) <= 12)
        head = index == 0 and sizes[0] == 3 and first_label.casefold() in ("fasa", "phase")
        for col, cell in enumerate(cells):
            cpr = cell.find(W + "tcPr")
            if cpr is None:
                cpr = etree.Element(W + "tcPr")
                cell.insert(0, cpr)
                changed = True
            shade = strong if head else tone if col == 0 and label_cell else None
            if shade:
                _, did = _set(cpr, "shd", {"val": "clear", "fill": shade})
                changed |= did
            margin, did = _set(cpr, "tcMar", {})
            changed |= did
            for side, amount in (("top", "45"), ("bottom", "45"), ("left", "65"), ("right", "65")):
                _, did = _set(margin, side, {"w": amount, "type": "dxa"})
                changed |= did
            if (col == 0 and label_cell) or head:
                for run in cell.iter(W + "r"):
                    rpr = run.find(W + "rPr")
                    if rpr is None:
                        rpr = etree.Element(W + "rPr")
                        run.insert(0, rpr)
                        changed = True
                    _, did = _set(rpr, "b", {"val": "1"})
                    changed |= did
                    if any("\u0600" <= c <= "\u08ff" for c in _text(run)):
                        _, did = _set(rpr, "bCs", {"val": "1"})
                        changed |= did
    return changed

def polish_kssr_word(document: BytesIO, subject: str) -> BytesIO:
    """Cosmetic only; fail safe to original BytesIO for any unverified shape."""
    if etree is None or not isinstance(document, BytesIO) or not isinstance(subject, str):
        return document
    key = ALIASES.get(subject.upper(), subject.upper())
    colors = _palettes().get(key)
    if not colors:
        return document
    raw = document.getvalue()
    if not (1000 <= len(raw) <= MAX_FILE and raw.startswith(b"PK\x03\x04")):
        return document
    try:
        with ZipFile(BytesIO(raw)) as z:
            members = z.infolist()
            names = [m.filename for m in members]
            if (len(members) > 300 or len(names) != len(set(names))
                    or DOC not in names or z.getinfo(DOC).file_size > MAX_XML
                    or z.testzip() is not None):
                return document
            parser = etree.XMLParser(resolve_entities=False, no_network=True)
            root = etree.fromstring(z.read(DOC), parser=parser)
            before = tuple(n.text for n in root.iter(W + "t"))
            prose = " ".join((n or "") for n in before).casefold()
            if not any(marker in prose for marker in SENTINELS):
                return document
            tables = list(root.iter(W + "tbl"))
            if len(tables) > 50 or not tables:
                return document
            labels = [_text(row.findall(W + "tc")[0]).casefold()
                      for table in tables for row in table.findall(W + "tr")
                      if row.findall(W + "tc")]
            if len({name for name in LABELS if any(name in val for val in labels)}) < 2:
                return document
            changed = sum(_style(table, *colors) for table in tables)
            if not changed:
                return document
            if before != tuple(n.text for n in root.iter(W + "t")):
                return document
            updated = etree.tostring(root, encoding="UTF-8",
                                     xml_declaration=True, standalone=True)
            out = BytesIO()
            with ZipFile(out, "w") as dst:
                for info in members:
                    dst.writestr(info, updated if info.filename == DOC else z.read(info.filename))
        result = out.getvalue()
        if not (1000 <= len(result) <= MAX_FILE):
            return document
        with ZipFile(BytesIO(result)) as check:
            if check.testzip() is not None:
                return document
            valid = etree.fromstring(check.read(DOC), parser=etree.XMLParser(
                resolve_entities=False, no_network=True))
            if before != tuple(n.text for n in valid.iter(W + "t")):
                return document
        return BytesIO(result)
    except (Exception):
        # Cosmetic failure cannot corrupt a lesson or prevent its download.
        return document
