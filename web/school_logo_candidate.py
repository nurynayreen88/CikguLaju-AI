"""User-scoped candidate school logos from GovTech Sekolahku's public fallback files.

The authenticated teacher's saved school code selects the candidate from the
private Storage catalog, with the pinned source as a fallback for missing files.
The candidate is kept separate from the teacher's personal logo.
"""
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from web.school_directory_store import (
    _read, school_by_code, SchoolDirectoryUnavailable,
)
from web.school_logo_store import BUCKET
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
        return _risalah_candidate(url, service_key, school_code, opener=opener)
    if len(rows) != 1 or rows[0].get("school_code") != school_code:
        raise LogoSourceUnavailable("Rekod logo tidak sepadan")
    ext, commit = rows[0].get("image_extension"), rows[0].get("source_commit")
    if ext not in MIME or commit != UPSTREAM_COMMIT:
        raise LogoSourceUnavailable("Sumber logo belum disahkan")
    if school_code in {"PBA1015", "YBB1418"}:
        return _risalah_candidate(url, service_key, school_code, opener=opener)
    filename = school_code + "." + ext
    try:
        blob = _catalog_image(url, service_key, commit, filename, ext, opener=opener)
    except LogoSourceUnavailable:
        blob = None
    if blob is None:
        req = Request(UPSTREAM_ROOT + filename, headers={
            "Accept": MIME[ext], "User-Agent": "CikguLaju-SchoolLogo/1.0",
        }, method="GET")
        try:
            blob = _image(req, ext, opener=opener)
        except HTTPError as exc:
            if exc.code in (403, 404):
                return None
            raise LogoSourceUnavailable("Sumber logo tidak dapat dihubungi") from None
    return blob, MIME[ext]


def _risalah_candidate(url, key, school_code, *, opener=None):
    image = _catalog_image(url, key, "risalahmap", school_code + ".png", "png", opener=opener)
    return (image, MIME["png"]) if image is not None else None


def _catalog_image(url, key, version, filename, ext, *, opener=None):
    parts = urlsplit(url)
    if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
            or parts.port is not None or parts.path not in ("", "/") or parts.query or parts.fragment):
        raise LogoSourceUnavailable("Konfigurasi storan logo tidak sah")
    path = f"/storage/v1/object/authenticated/{BUCKET}/school-logo-catalog/{version}/{filename}"
    request = Request(url.rstrip("/") + path, headers={
        "apikey": key, "Authorization": "Bearer " + key, "Accept": MIME[ext],
    })
    try:
        return _image(request, ext, opener=opener)
    except HTTPError as exc:
        if exc.code in (400, 404):
            return None
        raise LogoSourceUnavailable("Katalog logo belum tersedia") from None


def _image(req, ext, *, opener=None):
    try:
        with (opener or build_opener(NoRedirect())).open(req, timeout=9) as response:
            if response.status != 200:
                raise LogoSourceUnavailable("Sumber logo tidak dapat dibaca")
            length = response.headers.get("Content-Length")
            if length and (not length.isdecimal() or int(length) > MAX_SOURCE_BYTES):
                raise LogoSourceUnavailable("Fail logo terlalu besar")
            blob = response.read(MAX_SOURCE_BYTES + 1)
    except HTTPError:
        raise
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
    return blob
