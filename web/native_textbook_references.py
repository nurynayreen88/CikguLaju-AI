"""Provide checked Science textbook page selections and private PDF copies."""
import os
import re
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from web.native_telegram_extra_materials_20261106 import MAX_PDF
from web.native_telegram_rph_client import BlockRedirects
from web.native_telegram_sequence_rph_client import list_native_lessons

SCIENCE_PAGES = {
    1: {44: (2, 3), 45: (4, 5), 46: (6, 8), 47: (7, 8)},
    2: {52: (2, 4), 53: (5, 7), 54: (8, 9), 55: (10, 11), 56: (12, 14),
        57: (12, 14), 58: (18, 20)},
    3: {46: (2, 3), 47: (4, 5), 48: (6, 7), 49: (9, 10), 50: (11, 12), 51: (13, 14),
        52: (16, 19), 53: (20, 20), 54: (24, 27)},
    5: {84: (2, 7), 85: (2, 7), 86: (8, 13), 87: (8, 13), 88: (10, 13)},
    6: {85: (2, 5), 86: (5, 7), 87: (6, 7), 88: (7, 8), 89: (7, 8)},
}

SCIENCE_SOURCE = {
    1: (7, 66542795, "0edddd446f02c2b4e0ed2ffec34cbf03366aa60de439f95283cb3de2016e9727",
        "Alias bin Puteh, Jong Tze Kian, Mohd Ramadhan bin Anwar", 2016),
    2: (5, 79464408, "cf2e00ba3fc77290dd4298d563faf7e0b352343301120ecf962b735f342d366b",
        "Suwaibatullaslamiah binti Jalaludin, Mohd Ramadhan bin Anwar, Abdul Karim bin Daud", 2017),
    3: (7, 100100997, "5c5c95276915abfc52dab3515040064502cf10e8fcc4e1682648b9ee260f1cb8",
        "Mohd Faizal bin Rus Rzerli, Raja Shahida binti Raja Mansor, Abdul Karim bin Daud, Jong Tze Kian", 2018),
    5: (7, 91275648, "322b8ea0e19fc5b6da1c41ff64a25d22e470917027d9b293c85efc045a6be3e2",
        "Siti Roha binti Abd Karim, Mohd Ramadhan bin Anwar, Suwaibatullaslamiah binti Jalaludin", 2020),
    6: (6, 89740363, "7ee61a04efcf34fe45dc33d4c7d765c401566d1de69ff21764b5e3b3f7d6c228",
        "Suwaibatullaslamiah binti Jalaludin, Mohd Ramadhan bin Anwar, Jong Tze Kian", 2021),
}


def local_science_copy(year, lesson, pages):
    first, _, last = pages.partition("–")
    first, last = int(first), int(last or first)
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
    source_mapped = year in (2, 3) and re.fullmatch(rf"SCI-Y{year}-PDP-[0-9]{{3}}", lesson)
    if pages is None and not source_mapped:
        return None
    rows = list_native_lessons(year, "SCIENCE", unit)
    matches = [row for row in rows if row["value"] == lesson]
    if len(matches) != 1:
        return None
    row = matches[0]
    if source_mapped:
        printed = row.get("science_copy_pages")
        if not isinstance(printed, str):
            return None
        match = re.fullmatch(r"([1-9][0-9]?)(?:–([1-9][0-9]?))?", printed)
        if not match or row.get("textbook_ref") != f"Buku Teks m/s {printed}":
            return None
        first, last = int(match[1]), int(match[2] or match[1])
        if not first <= last <= first + 5:
            return None
        return printed, None
    first, last = pages
    printed = str(first) if first == last else f"{first}–{last}"
    if row.get("textbook_ref") != f"Buku Teks m/s {printed}":
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
