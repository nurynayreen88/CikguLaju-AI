"""Fail-closed private source adapter for KP2027 Tahun 1 Alam Lesson V10.

This does NOT register an HTTP endpoint, grant download permission or debit
credits. A server-side caller must first verify session, lesson entitlement,
content approval, and durable idempotent charging. The current archive is QA,
so delivery stays disabled even if its bytes are present in private Storage.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
import re
from urllib.parse import urlsplit
from zipfile import BadZipFile, ZipFile

BUCKET = "cikgulaju-materials"
OBJECT = "kp2027/sk/tahun-1/alam/v10/64-lesson-word-pdf.zip"
BYTES = 4_673_901
SHA256 = "b1ae8dcab0894bacc894d7fb310ff5ece27a1077e84846a64a86a61235d3a8ef"
PROJECT_HOST = "soxakntcanbycjoygrcx.supabase.co"
LESSONS = 64
COMBINED_LESSONS = 19
STATUS_QA = "QA_HOLD_NOT_WEB_LIVE"
MIMES = {
    "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}


class KP2027ArchiveUnavailable(Exception):
    """Archive or authorization evidence missing; do not fall back to Drive."""


def lesson_number(value):
    """Accept only a real lesson identifier, never a pathname or a bool."""
    if type(value) is int:
        number = value
    elif isinstance(value, str) and re.fullmatch(r"(?:[1-9]|[1-5][0-9]|6[0-4]|0[0-5][0-9]|06[0-4])", value):
        number = int(value)
    else:
        raise ValueError("Invalid KP2027 Lesson number")
    if not 1 <= number <= LESSONS:
        raise ValueError("Unknown KP2027 Lesson")
    return number


def verify_qa_archive(data):
    """Verify exact immutable source, complete members and per-file digests.

    Returns a handle over the in-memory bytes for internal offline QA only.
    Success never means academic approval or authorization to distribute.
    """
    if not isinstance(data, bytes) or len(data) != BYTES or sha256(data).hexdigest() != SHA256:
        raise KP2027ArchiveUnavailable("KP2027 archive integrity mismatch")
    try:
        archive = ZipFile(BytesIO(data))
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise KP2027ArchiveUnavailable("KP2027 archive corrupt or ambiguous")
        expected = {f"{folder}/ALAM_T1_LESSON{i:03d}.{ext}"
                    for folder, ext in (("Word", "docx"), ("PDF", "pdf"))
                    for i in range(1, LESSONS + 1)}
        expected |= {
            "QA_MANIFEST_LESSON_V10.json",
            "CIKGULAJU_KP2027_ALAM_T1_64_LESSON_V10_PADAN_A_B_QA_20261122.csv",
            "BACA_DULU_V10.txt",
        }
        if set(names) != expected:
            raise KP2027ArchiveUnavailable("Unexpected KP2027 archive contents")
        manifest = json.loads(archive.read("QA_MANIFEST_LESSON_V10.json"))
        if (manifest.get("status") != STATUS_QA
                or manifest.get("rpt_lessons") != LESSONS
                or manifest.get("combined_two_sp_lessons") != COMBINED_LESSONS
                or manifest.get("single_sp_lessons") != LESSONS - COMBINED_LESSONS
                or not isinstance(manifest.get("items"), list)
                or len(manifest["items"]) != LESSONS):
            raise KP2027ArchiveUnavailable("Unrecognized KP2027 QA manifest")
        seen = set()
        together = 0
        for item in manifest["items"]:
            n = item.get("lesson")
            if type(n) is not int or not 1 <= n <= LESSONS or n in seen:
                raise KP2027ArchiveUnavailable("Bad lesson manifest identity")
            seen.add(n)
            codes = item.get("codes")
            if (not isinstance(codes, list) or not (1 <= len(codes) <= 2)
                    or item.get("two_sp") is not (len(codes) == 2)
                    or any(not isinstance(c, str) or not re.fullmatch(r"[1-9]\.\d+\.\d+", c) for c in codes)
                    or item.get("pdf_pages") != 1
                    or item.get("status") != "QA_HOLD_ACADEMIC_WEB_E2E"):
                raise KP2027ArchiveUnavailable("Bad SP/approval manifest")
            together += len(codes) == 2
            for fmt, folder, ext, digest_key in (
                    ("word", "Word", "docx", "word_sha256"),
                    ("pdf", "PDF", "pdf", "pdf_sha256")):
                filename = f"{folder}/ALAM_T1_LESSON{n:03d}.{ext}"
                document = archive.read(filename)
                if not 1000 <= len(document) <= 10_000_000:
                    raise KP2027ArchiveUnavailable("Bad document size")
                if sha256(document).hexdigest() != item.get(digest_key):
                    raise KP2027ArchiveUnavailable("Document checksum mismatch")
                if fmt == "pdf" and not document.startswith(b"%PDF-"):
                    raise KP2027ArchiveUnavailable("Document PDF signature mismatch")
                if fmt == "word":
                    try:
                        with ZipFile(BytesIO(document)) as word:
                            if word.testzip() is not None or "word/document.xml" not in word.namelist():
                                raise KP2027ArchiveUnavailable("Bad Word document")
                    except BadZipFile as exc:
                        raise KP2027ArchiveUnavailable("Bad Word document") from exc
        if seen != set(range(1, LESSONS + 1)) or together != COMBINED_LESSONS:
            raise KP2027ArchiveUnavailable("Incomplete KP2027 Lesson/SP set")
        return archive
    except (BadZipFile, KeyError, TypeError, ValueError, OSError) as exc:
        if isinstance(exc, KP2027ArchiveUnavailable):
            raise
        raise KP2027ArchiveUnavailable("KP2027 archive cannot be verified") from exc


def _private_settings(config):
    """Refuse untrusted storage host, redirect, anonymous/public or browser URL."""
    if not isinstance(config, dict):
        raise KP2027ArchiveUnavailable("Storage configuration missing")
    base = str(config.get("supabase_url") or "").rstrip("/")
    secret = config.get("supabase_key")
    parts = urlsplit(base)
    if (parts.scheme != "https" or parts.hostname != PROJECT_HOST
            or parts.port is not None or parts.path not in ("", "/")
            or parts.username or parts.password or parts.query or parts.fragment
            or not isinstance(secret, str) or len(secret) < 30):
        raise KP2027ArchiveUnavailable("Storage credentials missing")
    return base, secret


def _read_private_source(config, opener=None):
    from urllib.request import Request, build_opener, HTTPRedirectHandler
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    base, key = _private_settings(config)
    url = f"{base}/storage/v1/object/authenticated/{BUCKET}/{OBJECT}"
    req = Request(url, headers={"Authorization": "Bearer " + key,
                                "apikey": key, "Accept": "application/zip"}, method="GET")
    try:
        open_request = opener or build_opener(NoRedirect()).open
        with open_request(req, timeout=40) as response:
            if getattr(response, "status", None) != 200:
                raise KP2027ArchiveUnavailable("Private archive not available")
            raw = response.read(BYTES + 1)
        return verify_qa_archive(raw)
    except KP2027ArchiveUnavailable:
        raise
    except (OSError, ValueError) as exc:
        raise KP2027ArchiveUnavailable("Private archive not available") from exc


def load_approved_document(lesson, fmt, *, config, approved=False, opener=None):
    """Fail closed until independent academic QA AND Web E2E release are signed.

    This method is intentionally unreachable for current V10 QA files. A new
    approved artifact/manifest and explicitly reviewed release code are required
    before connecting a public route. Never return QA bytes to an HTTP caller.
    """
    n = lesson_number(lesson)
    if fmt not in MIMES:
        raise ValueError("Invalid KP2027 document format")
    if approved is not True:
        raise KP2027ArchiveUnavailable("KP2027 is in academic QA")
    archive = _read_private_source(config, opener=opener)
    # Current source manifest is explicitly QA_HOLD, even with approved=True.
    manifest = json.loads(archive.read("QA_MANIFEST_LESSON_V10.json"))
    if manifest["items"][n - 1]["status"] != "WEB_RELEASE_APPROVED":
        raise KP2027ArchiveUnavailable("Web release approval absent")
    folder, ext = ("Word", "docx") if fmt == "word" else ("PDF", "pdf")
    return archive.read(f"{folder}/ALAM_T1_LESSON{n:03d}.{ext}"), MIMES[fmt]
