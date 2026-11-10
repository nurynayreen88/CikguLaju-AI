"""Read-only final-document quality check for Mathematics Web RPH.

Runs AFTER Telegram's real Word/PDF rendering but BEFORE the Web's atomic
trial debit. It does not rewrite curriculum, lesson content, lesson duration,
teacher metadata or any document bytes. Only independently demonstrable
defects block delivery; ambiguous layouts remain for a separate academic
review rather than having fabricated "repairs" applied automatically.
"""
from __future__ import annotations

from io import BytesIO
import re


class MathQualityReadError(ValueError):
    """Unable to inspect the generated document safely."""


_GENERIC = re.compile(
    r"menunjukkan\s+pengetahuan\s+atau\s+kemahiran\s+berdasarkan|"
    r"mencapai\s+(?:kemahiran|objektif)\s+berdasarkan\s+standard",
    flags=re.IGNORECASE,
)
_DUPLICATE_SK = re.compile(
    r"(?<![\d.])(\d{1,2}\.\d{1,2})[ \t]+\1(?![\d.])"
)
_SLOT = re.compile(
    r"^\s*([01]?\d|2[0-3]):([0-5]\d)\s*[-–—]\s*"
    r"([01]?\d|2[0-3]):([0-5]\d)\s*$"
)
_PHASE = re.compile(
    r"^\s*(?:\d{1,2}\s*[.)]\s*)?"
    r"(Set\s+Induksi|Aktiviti\s+[1-9]\d*|Pengukuhan|Penilaian|Penutup)"
    r"\b",
    flags=re.IGNORECASE,
)
_MINUTES = re.compile(r"(?<!\d)(\d{1,3})\s*minit\b", re.IGNORECASE)


def _read_text(fmt: str, data: bytes) -> str | None:
    """Read Word using Python stdlib only; PDF parser is optional on Web.

    Render Web currently installs only Flask/Gunicorn, not python-docx or
    pypdf. An absent PDF parser must not make every Mathematics download fail.
    The Telegram backend will separately enforce PDF content review.
    """
    if not isinstance(data, bytes) or not data:
        raise MathQualityReadError("Empty RPH bytes")
    try:
        if fmt == "word":
            from zipfile import ZipFile
            from xml.etree import ElementTree as ET
            with ZipFile(BytesIO(data)) as archive:
                if archive.testzip() or "word/document.xml" not in archive.namelist():
                    raise MathQualityReadError("Invalid Word archive")
                root = ET.fromstring(archive.read("word/document.xml"))
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            text = []
            for paragraph in root.findall(".//w:p", ns):
                words = [element.text or "" for element in paragraph.findall(".//w:t", ns)]
                text.append("".join(words))
            extracted = "\n".join(text)
        elif fmt == "pdf":
            try:
                from pypdf import PdfReader
            except ImportError:
                # No PDF extractor installed on the small Web service.
                # Preserve download availability rather than returning a
                # false content diagnosis or charging on an exception.
                return None
            pdf = PdfReader(BytesIO(data))
            if not 1 <= len(pdf.pages) <= 10:
                raise MathQualityReadError("Unexpected PDF page count")
            extracted = "\n".join(page.extract_text() or "" for page in pdf.pages)
        else:
            raise MathQualityReadError("Unsupported document format")
    except MathQualityReadError:
        raise
    except Exception as exc:
        raise MathQualityReadError("Document text cannot be inspected") from exc
    if len(extracted.strip()) < 30:
        raise MathQualityReadError("No readable lesson text")
    return extracted

def _slot_minutes(raw: object) -> int | None:
    if not isinstance(raw, str):
        return None
    match = _SLOT.fullmatch(raw)
    if not match:
        return None
    h1, m1, h2, m2 = map(int, match.groups())
    duration = (h2 * 60 + m2) - (h1 * 60 + m1)
    return duration if 1 <= duration <= 240 else None


def _explicit_phase_minutes(text: str) -> dict[str, int]:
    """Count explicitly labelled distinct teaching phases, never inferred time.

    Phase headings may be absent or formatted differently; a missing heading
    is not proof that a lesson is too short. Avoid adding both a section total
    and its subsection times by considering only Set Induksi, numbered
    Aktiviti, Pengukuhan, Penilaian and Penutup.
    """
    phases: dict[str, int] = {}
    for line in text.splitlines():
        match = _PHASE.match(line)
        if match is None:
            continue
        durations = _MINUTES.findall(line)
        if len(durations) != 1:
            continue
        minutes = int(durations[0])
        if not 1 <= minutes <= 120:
            continue
        key = re.sub(r"\s+", " ", match.group(1)).casefold()
        # Repeated PDF headings/tables must never be double counted.
        phases.setdefault(key, minutes)
    return phases


def inspect_math_rph_document(selection: dict, fmt: str, data: bytes) -> dict:
    """Return issues from actual downloaded bytes; no auto-repair or debit.

    Only the native MATEMATIK PdP pathway is inspected. Other subjects must
    keep their original route and source, including Sains and Islamic/Jawi.
    """
    if (not isinstance(selection, dict) or selection.get("subject") != "MATH"
            or selection.get("source") != "telegram-native-pdp-sequence"):
        return {"issues": [], "slot_minutes": None, "phase_minutes": None}
    text = _read_text(fmt, data)
    if text is None:
        return {"issues": [], "slot_minutes": None, "phase_minutes": None,
                "inspection": "PDF_PARSER_UNAVAILABLE"}
    issues: list[str] = []
    if _GENERIC.search(text):
        issues.append("GENERIC_OBJECTIVE")
    if _DUPLICATE_SK.search(text):
        issues.append("DUPLICATE_SK_DISPLAY")

    teacher = selection.get("teacher")
    slot = _slot_minutes(teacher.get("time") if isinstance(teacher, dict) else None)
    phases = _explicit_phase_minutes(text)
    total = sum(phases.values()) if len(phases) >= 4 else None
    # A partial or unlabelled phase set is inconclusive; do not invent a
    # duration error. A fully explicit overrun is conclusive.
    if slot is not None and total is not None and total > slot:
        issues.append("EXPLICIT_PHASES_EXCEED_SLOT")
    return {
        "issues": issues,
        "slot_minutes": slot,
        "phase_minutes": total,
        "explicit_phase_count": len(phases),
    }
