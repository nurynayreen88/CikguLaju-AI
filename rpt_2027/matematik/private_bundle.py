"""Decode the private Matematik RPT v28 archive from Render environment chunks.

This avoids committing paid PDF bytes into the public GitHub repository.
The archive is checksummed and only explicitly expected PDFs are extracted.
The environment values must be configured separately from source code.
"""
import base64
from functools import lru_cache
import hashlib
from io import BytesIO
import os
from pathlib import Path
import tempfile
import zipfile

ARCHIVE_SHA256 = "28e3a500c338f39df2f93b13ce6fb1d88ab5ed62311fa39fca024d6b211731fe"
PREFIX = "CIKGULAJU_RPT_MATH_B64_"
NAMES = frozenset("RPT_Matematik_Tahun_%d_2027_v28_SEMENTARA.pdf" % n for n in range(2, 7))
EXPECTED_ARCHIVE_SIZE = 907011
MAX_UNCOMPRESSED_FILE = 1024 * 1024


@lru_cache(maxsize=1)
def private_pdf_root():
    """Return local extracted PDF directory, or None on any validation failure."""
    raw_count = os.environ.get(PREFIX + "PARTS", "")
    if not raw_count.isascii() or not raw_count.isdecimal():
        return None
    n = int(raw_count)
    if not 1 <= n <= 64:
        return None
    parts = [os.environ.get(PREFIX + "%03d" % i, "") for i in range(n)]
    if not all(parts) or any(len(part) > 65536 for part in parts):
        return None
    try:
        data = base64.b64decode("".join(parts), validate=True)
        if len(data) != EXPECTED_ARCHIVE_SIZE:
            return None
        if hashlib.sha256(data).hexdigest() != ARCHIVE_SHA256:
            return None

        with zipfile.ZipFile(BytesIO(data)) as archive:
            entries = {entry.filename: entry for entry in archive.infolist()}
            if not NAMES.issubset(entries):
                return None
            pdf_bytes = {}
            for name in NAMES:
                info = entries[name]
                if info.is_dir() or info.file_size > MAX_UNCOMPRESSED_FILE:
                    return None
                contents = archive.read(info)
                if len(contents) < 100000 or contents[:5] != b"%PDF-":
                    return None
                pdf_bytes[name] = contents

        directory = Path(tempfile.mkdtemp(prefix="cikgulaju-rpt-math-v28-"))
        for name, contents in pdf_bytes.items():
            (directory / name).write_bytes(contents)
        return directory
    except (OSError, ValueError, zipfile.BadZipFile, EOFError, OverflowError):
        return None
