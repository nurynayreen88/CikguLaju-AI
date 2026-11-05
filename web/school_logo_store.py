"""Private school logo asset, scoped to the authenticated Telegram user.

Logos live in an isolated school-logos/ prefix in CikguLaju's EXISTING
private Supabase Storage bucket. No local ephemeral files, public links,
additional tables, overwrite of curricular PDFs, or browser service keys.
"""
from io import BytesIO
from struct import unpack
from zlib import crc32, decompressobj, error as ZlibError
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
    """Accept compact 8-bit RGBA/RGB PNG only; strip every ancillary chunk.

    Browsers convert JPG/WebP and resize through canvas before upload. This
    parser checks chunk CRCs, pixel bounds and decompressed scanline length
    without requiring extra packages in the dedicated Web deployment.
    """
    if not isinstance(source, bytes) or not 0 < len(source) <= MAX_INPUT:
        raise ProfileValidation("Logo mesti imej berukuran maksimum 2 MB")
    signature = b"\x89PNG\r\n\x1a\n"
    if not source.startswith(signature):
        raise ProfileValidation("Pilih logo PNG (JPG/WebP ditukar automatik)")
    pos, header, chunks, compressed, finished = 8, None, [], bytearray(), False
    while pos + 12 <= len(source):
        length = unpack(">I", source[pos:pos + 4])[0]
        name = source[pos + 4:pos + 8]
        if length > MAX_INPUT or pos + 12 + length > len(source):
            raise ProfileValidation("Struktur fail logo tidak sah")
        payload = source[pos + 8:pos + 8 + length]
        checksum = unpack(">I", source[pos + 8 + length:pos + 12 + length])[0]
        if crc32(name + payload) & 0xffffffff != checksum:
            raise ProfileValidation("Fail PNG rosak")
        pos += 12 + length
        if name == b"IHDR":
            if header is not None or length != 13 or chunks:
                raise ProfileValidation("Header PNG tidak sah")
            width, height, bit_depth, color, compression, filtering, interlace = unpack(">IIBBBBB", payload)
            if (not 32 <= width <= 1024 or not 32 <= height <= 1024
                    or width * height > 1_048_576 or bit_depth != 8
                    or color not in (2, 6) or compression or filtering or interlace):
                raise ProfileValidation("Dimensi atau format logo tidak disokong")
            header = (width, height, color)
            chunks.append((name, payload))
        elif name == b"IDAT":
            if header is None or finished or len(compressed) + length > MAX_SAVED:
                raise ProfileValidation("Data PNG tidak sah")
            compressed.extend(payload)
            chunks.append((name, payload))
        elif name == b"IEND":
            if length or header is None or not compressed or pos != len(source):
                raise ProfileValidation("Penamat PNG tidak sah")
            chunks.append((name, payload))
            finished = True
            break
        elif name in (b"sRGB", b"gAMA", b"pHYs", b"cHRM"):
            if header is None or compressed:
                raise ProfileValidation("Metadata PNG tidak sah")
            # Strip harmless color metadata. Never preserve author/EXIF/text.
        else:
            raise ProfileValidation("Sila gunakan logo PNG tanpa metadata tambahan")
    if not finished:
        raise ProfileValidation("Fail PNG tidak lengkap")
    width, height, color = header
    expected = (width * (4 if color == 6 else 3) + 1) * height
    try:
        obj = decompressobj()
        pixels = obj.decompress(bytes(compressed), expected + 1)
        if (len(pixels) != expected or not obj.eof or obj.unconsumed_tail
                or obj.unused_data or obj.flush()):
            raise ProfileValidation("Kandungan PNG tidak sah")
        stride = width * (4 if color == 6 else 3) + 1
        if any(pixels[i * stride] not in range(5) for i in range(height)):
            raise ProfileValidation("Penapis PNG tidak sah")
    except (ValueError, OverflowError, MemoryError, ZlibError):
        raise ProfileValidation("Kandungan PNG rosak") from None
    raw = bytearray(signature)
    for name, payload in chunks:
        raw.extend(len(payload).to_bytes(4, "big") + name + payload)
        raw.extend((crc32(name + payload) & 0xffffffff).to_bytes(4, "big"))
    if len(raw) > MAX_SAVED:
        raise ProfileValidation("Logo terlalu besar selepas diproses")
    return bytes(raw)

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
