"""User-scoped candidate school logos from GovTech Sekolahku's public fallback files.

CikguLaju retains metadata in Supabase, NOT a mass copy of third-party files.
The authenticated teacher's already-saved school code (not a browser-supplied
URL or code) selects the candidate. The browser can then convert the image
to PNG and store it in the teacher's existing PRIVATE Supabase Storage path.
Never overwrite a previously uploaded logo without a user decision.
"""
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from web.school_directory_store import (
    _read, school_by_code, SchoolDirectoryUnavailable,
)
from web.teacher_profile_store import NoRedirect

UPSTREAM_COMMIT = "2fa79e15e77da39371138bc247dc034d17a90b4b"
UPSTREAM_ROOT = (
    "https://raw.githubusercontent.com/govtechmy/sekolahku-fe/"
    + UPSTREAM_COMMIT + "/public/logo-sekolah/"
)
MAX_SOURCE_BYTES = 2 * 1024 * 1024
CODE = re.compile(r"[A-Z0-9]{6,12}\Z")
MIME = {"jpg": "image/jpeg", "png": "image/png", "gif": "image/gif"}


class LogoSourceUnavailable(Exception):
    pass


def logo_candidate(url, service_key, school_code, *, opener=None):
    """Return (bytes, MIME) or None; never accepts a source URL from callers.

    The school lookup checks level=Rendah and the source registry is read-only
    to the authenticated server. Upstream failures do not modify prior logos.
    """
    if not isinstance(school_code, str) or not CODE.fullmatch(school_code):
        return None
    try:
        school = school_by_code(url, service_key, school_code, opener=opener)
    except ValueError:
        return None
    except SchoolDirectoryUnavailable:
        raise LogoSourceUnavailable("Direktori sekolah belum dapat disemak") from None
    if school.get("school_level") != "Rendah":
        return None
    try:
        rows = _read(url, service_key, "school_logo_sources", {
            "select": "school_code,image_extension,source_commit",
            "school_code": "eq." + school_code,
        }, limit=2, opener=opener)
    except SchoolDirectoryUnavailable:
        raise LogoSourceUnavailable("Senarai logo belum tersedia") from None
    if not rows:
        return None
    if len(rows) != 1 or rows[0].get("school_code") != school_code:
        raise LogoSourceUnavailable("Rekod logo tidak sepadan")
    ext, commit = rows[0].get("image_extension"), rows[0].get("source_commit")
    if ext not in MIME or commit != UPSTREAM_COMMIT:
        raise LogoSourceUnavailable("Sumber logo belum disahkan")
    source_url = UPSTREAM_ROOT + school_code + "." + ext
    req = Request(source_url, headers={
        "Accept": MIME[ext], "User-Agent": "CikguLaju-SchoolLogo/1.0",
    }, method="GET")
    try:
        # No redirects: never follow a third-party Location to a new host.
        with (opener or build_opener(NoRedirect())).open(req, timeout=9) as response:
            if response.status != 200:
                raise LogoSourceUnavailable("Sumber logo tidak dapat dibaca")
            length = response.headers.get("Content-Length")
            if length and (not length.isdecimal() or int(length) > MAX_SOURCE_BYTES):
                raise LogoSourceUnavailable("Fail logo terlalu besar")
            blob = response.read(MAX_SOURCE_BYTES + 1)
    except HTTPError as exc:
        if exc.code in (403, 404):
            return None
        raise LogoSourceUnavailable("Sumber logo tidak dapat dihubungi") from None
    except (URLError, OSError, TimeoutError):
        raise LogoSourceUnavailable("Sumber logo tidak dapat dihubungi") from None
    if not 0 < len(blob) <= MAX_SOURCE_BYTES:
        raise LogoSourceUnavailable("Fail logo terlalu besar atau kosong")
    magic = {
        "jpg": blob.startswith(b"\xff\xd8\xff"),
        "png": blob.startswith(b"\x89PNG\r\n\x1a\n"),
        "gif": blob.startswith((b"GIF87a", b"GIF89a")),
    }
    if not magic[ext]:
        raise LogoSourceUnavailable("Kandungan sumber bukan imej sekolah yang sah")
    return blob, MIME[ext]
