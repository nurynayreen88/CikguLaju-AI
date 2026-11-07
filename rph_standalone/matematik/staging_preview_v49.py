"""Fail-closed preview of Matematik Years 2–6 RPH v49; STAGING ONLY.

This module is *not* imported by production. It does not change the curriculum
DB, Telegram menus, user records, subscriptions or free RPH quotas.
Opt-in install requires the explicit STAGING environment flag and an
independently mounted ZIP with an exact SHA-256 match.

The ZIP is intentionally not committed to the public GitHub repository.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import zipfile
from functools import lru_cache
from pathlib import Path

EXPECTED_SHA256 = "fcc3e7fe07ed6eb9cb0abdff1ef3bd1765c7050a6d8e036b81abd199ae4835b0"
STAGING_FLAG = "CIKGULAJU_MATH_RPH_V49_STAGING_PREVIEW"
CALLBACK_PREFIX = "mathrph_v49_preview_"
CALLBACK_RE = re.compile(r"^mathrph_v49_preview_y([2-6])_l(\d{3})_(pdf|docx)$")
YEARS = frozenset(range(2, 7))
FORMATS = {"pdf": "PDF", "docx": "Word"}


class PreviewUnavailable(RuntimeError):
    """Do not fall back to an arbitrary DB/file/year on missing evidence."""


def archive_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as data:
        for chunk in iter(lambda: data.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=8)
def _check_file(full_path, mtime_ns, size, expected_sha256):
    path = Path(full_path)
    if archive_sha256(path) != expected_sha256:
        raise PreviewUnavailable("Semakan SHA-256 arkib gagal")
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if len(set(names)) != len(names):
                raise PreviewUnavailable("Nama fail berulang")
            available = set(names)
            for year in YEARS:
                for lesson in range(1, 118):
                    for folder, ext in (("PDF", "pdf"), ("Word", "docx"), ("Markdown", "md")):
                        item = f"Tahun_{year}/{folder}/lesson_{lesson:03d}.{ext}"
                        if item not in available:
                            raise PreviewUnavailable(f"Fail Tahun {year} Lesson {lesson} tiada")
            gate = json.loads(z.read("AUDIT/V49_RELEASE_GATE.json").decode("utf-8"))
            if gate.get("rph_total") != 585 or gate.get("BA_year2_3_ref_count") != 234 or gate.get("final_ready") is not False:
                raise PreviewUnavailable("Metadata release gate tidak sepadan")
    except (OSError, zipfile.BadZipFile, KeyError, UnicodeDecodeError) as exc:
        raise PreviewUnavailable("Arkib tidak boleh dibaca") from exc
    return True


def verify_archive(archive_path, expected_sha256=None):
    if expected_sha256 is None:
        expected_sha256 = EXPECTED_SHA256
    if not archive_path:
        raise PreviewUnavailable("Lokasi arkib staging tiada")
    path = Path(archive_path)
    try:
        if not path.is_file() or path.stat().st_size < 100000:
            raise PreviewUnavailable("Fail staging tidak ditemui")
        s = path.stat()
        _check_file(str(path.resolve()), s.st_mtime_ns, s.st_size, expected_sha256)
        return path
    except OSError as exc:
        raise PreviewUnavailable("Fail staging tidak boleh dibaca") from exc


def extract_rph_bytes(archive_path, year, lesson, file_format, expected_sha256=None):
    if expected_sha256 is None:
        expected_sha256 = EXPECTED_SHA256
    # bool subclasses int and must be rejected to prevent ambiguous targets.
    if type(year) is not int or year not in YEARS:
        raise ValueError("Tahun Matematik tidak sah")
    if type(lesson) is not int or not (1 <= lesson <= 117):
        raise ValueError("Lesson Matematik tidak sah")
    if file_format not in FORMATS:
        raise ValueError("Format RPH tidak sah")
    path = verify_archive(archive_path, expected_sha256=expected_sha256)
    item = f"Tahun_{year}/{FORMATS[file_format]}/lesson_{lesson:03d}.{file_format}"
    try:
        with zipfile.ZipFile(path) as z:
            data = z.read(item)
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise PreviewUnavailable("RPH tidak tersedia; tiada sandaran automatik") from exc
    header = b"%PDF-" if file_format == "pdf" else b"PK\x03\x04"
    if len(data) < 500 or not data.startswith(header):
        raise PreviewUnavailable("Fail RPH tidak sah")
    return data


def install(ns, archive_path):
    """Only opt-in on isolated staging, never install on production by default."""
    if (os.environ.get(STAGING_FLAG) != "1"
            or os.environ.get("CIKGULAJU_ENVIRONMENT", "").lower() != "staging"):
        return False
    if ns.get("CIKGULAJU_MATH_RPH_V49_STAGING_INSTALLED"):
        return True
    required = ("callback", "send", "send_document", "_access_info", "_is_admin")
    if any(not callable(ns.get(name)) for name in required):
        return False
    previous = ns["callback"]
    send = ns["send"]
    send_document = ns["send_document"]

    def callback(chat_id, data):
        raw = str(data or "")
        if not raw.startswith(CALLBACK_PREFIX):
            return previous(chat_id, data)
        match = CALLBACK_RE.fullmatch(raw)
        if not match:
            return send(chat_id, "Pilihan RPH Matematik staging tidak sah.")
        year, lesson, fmt = int(match.group(1)), int(match.group(2)), match.group(3)
        if lesson < 1 or lesson > 117:
            return send(chat_id, "Nombor Lesson Matematik tidak sah.")
        try:
            authorized = bool(ns["_is_admin"](chat_id) or ns["_access_info"](chat_id).get("active"))
        except Exception:
            authorized = False
        if not authorized:
            return send(chat_id, "RPH Matematik staging hanya untuk pelanggan yang disahkan.")
        try:
            payload = extract_rph_bytes(archive_path, year, lesson, fmt)
            with tempfile.TemporaryDirectory(prefix="cikgulaju_math_staging_") as temp:
                out = Path(temp) / f"matematik_tahun{year}_lesson{lesson:03d}.{fmt}"
                out.write_bytes(payload)
                response = send_document(
                    chat_id, str(out),
                    f"RPH Matematik Tahun {year} Lesson {lesson:03d} — v49 STAGING",
                )
                checker = ns.get("_telegram_delivery_ok_v25279")
                confirmed = bool(checker(response)) if callable(checker) else bool(
                    getattr(response, "ok", False) and response.json().get("ok") is True
                )
                if not confirmed:
                    return send(chat_id, "Penghantaran fail staging belum disahkan oleh Telegram.")
                return response
        except (PreviewUnavailable, OSError, ValueError):
            return send(chat_id, "RPH Matematik staging tidak tersedia atau gagal semakan.")
        except Exception:
            return send(chat_id, "Penghantaran RPH Matematik staging gagal.")

    ns["callback"] = callback
    ns["CIKGULAJU_MATH_RPH_V49_STAGING_INSTALLED"] = True
    return True
