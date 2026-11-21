"""Conservative Word-only RPH activity-title styling at the download boundary.

The Telegram/native DOCX remains authoritative. This pass adds bold typography
only to an existing, standalone numbered activity heading inside a table.
It never inserts/removes text, line breaks, cells, paragraphs, or lesson data.
Unexpected Word structures return the original untouched document.
"""
from __future__ import annotations

from copy import deepcopy
from io import BytesIO
import re
from zipfile import ZipFile

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOC = "word/document.xml"
MAX_XML = 8 * 1024 * 1024
MAX_DOCX = 15 * 1024 * 1024

_HEADING = re.compile(
    r"^(?:Aktiviti|Activity)\s+[1-9]\d?"
    r"(?:\s*[:\-–—]\s*[^.!?\n]{1,75})?$",
    re.IGNORECASE,
)
_INSTRUCTION_START = re.compile(
    r"^(?:Guru|Murid|Teacher|Pupil|Pupils|Student|Students)\b",
    re.IGNORECASE,
)


def _is_activity_heading(value: str) -> bool:
    value = " ".join(value.split())
    if not _HEADING.fullmatch(value):
        return False
    remainder = re.sub(
        r"^(?:Aktiviti|Activity)\s+[1-9]\d?\s*[:\-–—]\s*",
        "", value, flags=re.IGNORECASE,
    )
    return remainder == value or not _INSTRUCTION_START.match(remainder)


def _make_bold(props) -> None:
    for local in ("b", "bCs"):
        el = props.find(W + local)
        if el is None:
            el = etree.Element(W + local)
            props.append(el)
        el.set(W + "val", "1")


def _change_paragraph(para) -> bool:
    # Protect complex Word markup and non-table prose against reflow.
    if not any(parent.tag == W + "tc" for parent in para.iterancestors()):
        return False
    if any(node.tag not in (W + "pPr", W + "r") for node in para):
        return False
    runs = para.findall(W + "r")
    if not runs or any(
        node.tag not in (W + "rPr", W + "t", W + "br")
        for run in runs for node in run
    ):
        return False
    lines = [[]]
    for run in runs:
        props = run.find(W + "rPr")
        for node in run:
            if node.tag == W + "rPr":
                continue
            lines[-1].append((props, node, dict(run.attrib)))
            if node.tag == W + "br":
                lines.append([])
    heading_lines = set()
    for idx, line in enumerate(lines):
        words = "".join(node.text or "" for _, node, _ in line if node.tag == W + "t")
        if words.strip() and _is_activity_heading(words.strip()):
            heading_lines.add(idx)
    if not heading_lines:
        return False
    original_words = tuple(node.text for node in para.iter(W + "t"))
    original_breaks = len(tuple(para.iter(W + "br")))
    already_bold = True
    for idx in heading_lines:
        for props, node, _ in lines[idx]:
            if node.tag != W + "t":
                continue
            if (props is None or props.find(W + "b") is None
                    or props.find(W + "b").get(W + "val") in ("0", "false")):
                already_bold = False
                break
    if already_bold:
        return False
    for run in runs:
        para.remove(run)
    for idx, line in enumerate(lines):
        for props, node, attrs in line:
            fresh = etree.Element(W + "r", attrib=attrs)
            properties = deepcopy(props) if props is not None else None
            if idx in heading_lines and node.tag == W + "t":
                if properties is None:
                    properties = etree.Element(W + "rPr")
                _make_bold(properties)
            if properties is not None:
                fresh.append(properties)
            fresh.append(node)
            para.append(fresh)
    if (tuple(node.text for node in para.iter(W + "t")) != original_words
            or len(tuple(para.iter(W + "br"))) != original_breaks):
        raise ValueError("Activity title formatting changed RPH text")
    return True


def style_word_activity_titles(document: BytesIO) -> BytesIO:
    """Return a new DOCX stream only when existing numbered headings are styled."""
    if not isinstance(document, BytesIO):
        return document
    original = document.getvalue()
    if not (1000 <= len(original) <= MAX_DOCX and original.startswith(b"PK\x03\x04")):
        return document
    try:
        with ZipFile(BytesIO(original)) as package:
            members = package.infolist()
            if (len(members) > 300 or DOC not in package.namelist()
                    or package.getinfo(DOC).file_size > MAX_XML
                    or package.testzip() is not None):
                return document
            root = etree.fromstring(
                package.read(DOC),
                parser=etree.XMLParser(resolve_entities=False, no_network=True),
            )
            before = tuple(node.text for node in root.iter(W + "t"))
            count = sum(_change_paragraph(para) for para in root.iter(W + "p"))
            if not count:
                return document
            if before != tuple(node.text for node in root.iter(W + "t")):
                raise ValueError("Activity formatter altered curriculum text")
            updated_xml = etree.tostring(
                root, encoding="UTF-8", xml_declaration=True, standalone=True,
            )
            output = BytesIO()
            with ZipFile(output, "w") as updated:
                for member in members:
                    updated.writestr(
                        member,
                        updated_xml if member.filename == DOC else package.read(member.filename),
                    )
            data = output.getvalue()
            if not (1000 <= len(data) <= MAX_DOCX):
                return document
            with ZipFile(BytesIO(data)) as check:
                if check.testzip() is not None:
                    return document
                valid = etree.fromstring(
                    check.read(DOC),
                    parser=etree.XMLParser(resolve_entities=False, no_network=True),
                )
                if before != tuple(node.text for node in valid.iter(W + "t")):
                    return document
            return BytesIO(data)
    except Exception:
        # Cosmetic failures must not block a teacher or consume extra credits.
        return document
