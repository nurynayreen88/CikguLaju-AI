"""Private school logo asset, scoped to the authenticated Telegram user.

Logos live in an isolated school-logos/ prefix in CikguLaju's EXISTING
private Supabase Storage bucket. No local ephemeral files, public links,
additional tables, overwrite of curricular PDFs, or browser service keys.
"""
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from web.teacher_profile_store import NoRedirect, ProfileUnavailable, ProfileValidation

BUCKET = "cikgulaju-materials"
MAX_INPUT = 2 * 1024 * 1024
MAX_SAVED = 450 * 1024


def _object_url(supabase_url, user_id):
    parsed = urlsplit(supabase_url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.port is not None
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment
            or parsed.username or parsed.password or type(user_id) is not int
            or user_id < 1):
        raise ProfileUnavailable("Konfigurasi storan tidak sah")
    return supabase_url.rstrip("/") + "/storage/v1/object/" + BUCKET + (
        "/school-logos/%d/logo.png" % user_id)


def normalized_png(source):
    """Strip metadata, reject vector/corrupt/animated images, limit pixels."""
    if not isinstance(source, bytes) or not 0 < len(source) <= MAX_INPUT:
        raise ProfileValidation("Logo mesti imej berukuran maksimum 2 MB")
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
        from PIL import ImageFile
        Image.MAX_IMAGE_PIXELS = 12_000_000
        ImageFile.LOAD_TRUNCATED_IMAGES = False
        with Image.open(BytesIO(source)) as picture:
            if picture.format not in ("PNG", "JPEG", "WEBP") or getattr(picture, "is_animated", False):
                raise ProfileValidation("Pilih logo PNG, JPG atau WebP tidak beranimasi")
            if picture.width < 32 or picture.height < 32:
                raise ProfileValidation("Logo terlalu kecil")
            if picture.width * picture.height > 12_000_000:
                raise ProfileValidation("Dimensi logo terlalu besar")
            picture.load()
            img = ImageOps.exif_transpose(picture).convert("RGBA")
        for side in (512, 420, 320, 240):
            candidate = img.copy()
            candidate.thumbnail((side, side), Image.Resampling.LANCZOS)
            stream = BytesIO()
            candidate.save(stream, format="PNG", optimize=True)
            result = stream.getvalue()
            if len(result) <= MAX_SAVED:
                return result
    except ProfileValidation:
        raise
    except (OSError, ValueError, TypeError, UnidentifiedImageError, Image.DecompressionBombError):
        pass
    raise ProfileValidation("Fail logo tidak sah atau tidak boleh diproses")


def logo_png(supabase_url, service_key, user_id, *, opener=None):
    if not service_key:
        raise ProfileUnavailable("Sambungan storan belum tersedia")
    request = Request(_object_url(supabase_url, user_id), headers={
        "apikey": service_key, "Authorization": "Bearer " + service_key,
        "Accept": "image/png",
    }, method="GET")
    try:
        with (opener or build_opener(NoRedirect())).open(request, timeout=8) as response:
            if response.status != 200:
                raise ProfileUnavailable("Storan logo tidak tersedia")
            value = response.read(MAX_SAVED + 1)
        if len(value) > MAX_SAVED or not value.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ProfileUnavailable("Logo tersimpan tidak sah")
        return value
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise ProfileUnavailable("Logo sekolah tidak dapat dibaca") from None
    except (OSError, URLError):
        raise ProfileUnavailable("Storan logo tidak dapat dihubungi") from None


def save_logo_png(supabase_url, service_key, user_id, raw, *, opener=None):
    png = normalized_png(raw)
    if not service_key:
        raise ProfileUnavailable("Sambungan storan belum tersedia")
    request = Request(_object_url(supabase_url, user_id), data=png, headers={
        "apikey": service_key, "Authorization": "Bearer " + service_key,
        "Content-Type": "image/png", "Content-Length": str(len(png)),
        "x-upsert": "true",
    }, method="POST")
    # Supabase's Storage upload endpoint supports POST /object/{bucket}/{path}
    try:
        with (opener or build_opener(NoRedirect())).open(request, timeout=10) as response:
            if response.status not in (200, 201):
                raise ProfileUnavailable("Storan logo tidak menerima fail")
            response.read(2048)
    except (HTTPError, URLError, OSError):
        raise ProfileUnavailable("Logo sekolah tidak berjaya disimpan. Logo lama dikekalkan.") from None
    return len(png)
