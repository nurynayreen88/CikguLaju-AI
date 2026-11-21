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

try:
    from lxml import etree
except ImportError:
    # Formatting is optional; the validated Telegram Word must stay usable.
    etree = None

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOC = "word/document.xml"
MAX_XML = 8 * 1024 * 1024
MAX_DOCX = 15 * 1024 * 1024

# Match standalone numbered activity headings from verified LTR, DLP, PPKI
# and RTL templates. Preserve all text and existing line breaks.
_NUMBER = r"[1-9١-٩][0-9٠-٩]{0,2}"
_LABEL = (
    r"(?:Aktiviti|Activity|Langkah|Step|اکتيۏيتي|اکتيۏيتی"
    r"|اكتيويتي|اكتيفيتي|النشاط|نشاط)"
)
_NUMBERED_LABEL = rf"{_LABEL}\s+{_NUMBER}"
_DURATION = rf"(?:\s*\(\s*{_NUMBER}\s*(?:minit|minutes?|mins?)\s*\))?"
_TITLE_BASE = rf"(?:[1-9]\d?[.)]\s*)?{_NUMBERED_LABEL}{_DURATION}"
_HEADING = re.compile(
    rf"^{_TITLE_BASE}(?:\s*[:：\-–—]\s*[^.!?\n]{{1,75}})?$",
    re.IGNORECASE,
)
_HEADING_PREFIX = re.compile(
    rf"^{_TITLE_BASE}\s*[:：\-–—]\s*", re.IGNORECASE,
)
_INSTRUCTION_START = re.compile(
    r"^(?:Guru|Murid|Pelajar|Teacher|Teachers|Pupil|Pupils|Student|Students"
    r"|ݢورو|ڬورو|موريد|المعلم|المعلمة|الطلاب|الطلبة)\b",
    re.IGNORECASE,
)


def _is_activity_heading(value: str) -> bool:
    value = " ".join(value.split())
    if not _HEADING.fullmatch(value):
        return False
    remainder = _HEADING_PREFIX.sub("", value)
    return remainder == value or not _INSTRUCTION_START.match(remainder)


def _make_bold(props) -> None:
    for local in ("b", "bCs"):
        el = props.find(W + local)
        if el is None:
            el = etree.Element(W + local)
            props.append(el)
        el.set(W + "val", "1")


def _change_paragraph(para) -> bool:
    # Keep native tab stops and either type of manual line break unchanged.
    # Protect complex Word markup and non-table prose against reflow.
    if not any(parent.tag == W + "tc" for parent in para.iterancestors()):
        return False
    if any(node.tag not in (W + "pPr", W + "r") for node in para):
        return False
    runs = para.findall(W + "r")
    if not runs or any(
        node.tag not in (W + "rPr", W + "t", W + "br", W + "cr", W + "tab")
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
            if node.tag in (W + "br", W + "cr"):
                lines.append([])
    heading_lines = set()
    for idx, line in enumerate(lines):
        words = "".join(node.text or "" for _, node, _ in line if node.tag == W + "t")
        if words.strip() and _is_activity_heading(words.strip()):
            heading_lines.add(idx)
    if not heading_lines:
        return False
    original_words = tuple(node.text for node in para.iter(W + "t"))
    original_breaks = tuple((len(tuple(para.iter(W + name))) for name in ("br", "cr", "tab")))
    already_bold = True
    for idx in heading_lines:
        for props, node, _ in lines[idx]:
            if node.tag != W + "t":
                continue
            # Arabic/Jawi headings also need complex-script bold (w:bCs).
            # A run with only Latin bold (w:b) may still render unbolded
            # when its visible letters use the Arabic script.
            strong = props.find(W + "b") if props is not None else None
            complex_strong = props.find(W + "bCs") if props is not None else None
            complex_script = (
                any("\u0600" <= ch <= "\u08ff" for ch in (node.text or ""))
                or (props is not None and props.find(W + "rtl") is not None)
            )
            if (strong is None or strong.get(W + "val") in ("0", "false")
                    or (complex_script and
                        (complex_strong is None or
                         complex_strong.get(W + "val") in ("0", "false")))):
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
            or tuple(len(tuple(para.iter(W + name))) for name in ("br", "cr", "tab")) != original_breaks):
        raise ValueError("Activity title formatting changed RPH text")
    return True


def style_word_activity_titles(document: BytesIO) -> BytesIO:
    """Return a new DOCX stream only when existing numbered headings are styled."""
    if etree is None or not isinstance(document, BytesIO):
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
