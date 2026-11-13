"""Serve checked Science textbook excerpts from private material storage."""
import os
import re
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from web.native_telegram_extra_materials_20261106 import MAX_PDF
from web.native_telegram_rph_client import BlockRedirects
from web.native_telegram_sequence_rph_client import list_native_lessons

SCIENCE_PAGES = {
    2: {52: (2, 4), 53: (5, 7), 54: (8, 9), 55: (10, 11), 56: (12, 14),
        57: (12, 14), 58: (18, 20)},
    3: {46: (2, 3), 47: (4, 5), 49: (9, 10), 50: (11, 12), 51: (13, 14),
        52: (16, 19), 53: (20, 20), 54: (24, 27)},
}

SCIENCE_SOURCE = {
    2: (5, 79464408, "cf2e00ba3fc77290dd4298d563faf7e0b352343301120ecf962b735f342d366b",
        "Suwaibatullaslamiah binti Jalaludin, Mohd Ramadhan bin Anwar, Abdul Karim bin Daud", 2017),
    3: (7, 100100997, "5c5c95276915abfc52dab3515040064502cf10e8fcc4e1682648b9ee260f1cb8",
        "Mohd Faizal bin Rus Rzerli, Raja Shahida binti Raja Mansor, Abdul Karim bin Daud, Jong Tze Kian", 2018),
}


def local_science_copy(year, lesson, pages):
    first, last = SCIENCE_PAGES[year][int(lesson.rsplit("-", 1)[1])]
    offset, size, digest, authors, edition = SCIENCE_SOURCE[year]
    return {
        "type": "textbook", "action": "local-pdf",
        "title": f"Salinan PdP Buku Teks Sains Tahun {year} • m/s {pages}",
        "pdf": {"size": size, "sha256": digest, "start": first + offset,
                "end": last + offset, "filename": f"CikguLaju_Sains_{lesson}_ms_{first}-{last}.pdf",
                "source": f"Sains Tahun {year} SK, Dewan Bahasa dan Pustaka ({edition}), m/s {pages}",
                "authors": authors},
    }


def textbook_reference(year, unit, lesson):
    match = re.fullmatch(rf"ST{year}-PDP-([0-9]{{3}})", lesson)
    pages = SCIENCE_PAGES.get(year, {}).get(int(match[1])) if match else None
    if pages is None:
        return None
    first, last = pages
    printed = str(first) if first == last else f"{first}–{last}"
    rows = list_native_lessons(year, "SCIENCE", unit)
    matches = [row for row in rows if row["value"] == lesson]
    if len(matches) != 1 or matches[0].get("textbook_ref") != f"Buku Teks m/s {printed}":
        return None
    path = f"buku-teks/sains/tahun-{year}/ms-{first}-{last}.pdf"
    return printed, path


def private_textbook_pdf(path, *, metadata_only=False):
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    secret = os.environ.get("SUPABASE_SECRET_KEY", "")
    bucket = os.environ.get("CIKGULAJU_MATERIAL_BUCKET", "cikgulaju-materials")
    origin = urlsplit(base)
    if (origin.scheme != "https" or not re.fullmatch(r"[a-z0-9]+\.supabase\.co", origin.netloc)
            or origin.path or origin.query or origin.fragment or not secret
            or not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", bucket)):
        return None
    if not re.fullmatch(r"buku-teks/sains/tahun-[23]/ms-[0-9]{1,2}-[0-9]{1,2}\.pdf", path):
        return None
    request = Request(f"{base}/storage/v1/object/authenticated/{bucket}/{path}",
                      method="HEAD" if metadata_only else "GET",
                      headers={"apikey": secret, "Authorization": f"Bearer {secret}"})
    try:
        with build_opener(BlockRedirects()).open(request, timeout=10) as response:
            if response.status != 200 or response.headers.get_content_type() != "application/pdf":
                return None
            if metadata_only:
                size = response.headers.get("Content-Length", "")
                return size.isdecimal() and 450 <= int(size) <= MAX_PDF
            data = response.read(MAX_PDF + 1)
            return data if 450 <= len(data) <= MAX_PDF and data.startswith(b"%PDF-") else None
    except HTTPError as error:
        if error.code == 404:
            return None
        raise
