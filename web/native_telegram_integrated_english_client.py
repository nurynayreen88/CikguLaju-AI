"""Requests a single integrated English plan from the private Telegram renderer."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from web.native_telegram_rph_client import BlockRedirects, NativeRPHUnavailable, MIMES
from web.native_verified_rpt_rph_client import _backend


def integrated_enabled():
    return os.environ.get("CIKGULAJU_ENGLISH_2027_INTEGRATED_RPH_ENABLED") == "1"


def request_integrated(data, fmt, *, opener=None):
    if fmt not in ("metadata", "word", "pdf"):
        raise ValueError("Unknown integrated RPH format")
    base, token = _backend()
    mime = "application/json" if fmt == "metadata" else MIMES[fmt]
    payload = {key: data[key] for key in ("year", "lesson", "unit", "teacher")}
    payload["format"] = fmt
    req = Request(urlsplit(base).geturl().rstrip("/") + "/internal/rph/v1/english-integrated",
                  data=json.dumps(payload, ensure_ascii=False).encode(), method="POST",
                  headers={"Authorization": "Bearer " + token, "Content-Type": "application/json",
                           "Accept": mime})
    limit = 1500 if fmt == "metadata" else 1_000_000
    try:
        with (opener or build_opener(BlockRedirects())).open(req, timeout=20) as response:
            if response.status != 200 or response.headers.get_content_type() != mime:
                raise NativeRPHUnavailable("Invalid integrated English response")
            content = response.read(limit + 1)
    except HTTPError as exc:
        if exc.code == 404 and fmt == "metadata":
            return None
        raise NativeRPHUnavailable("Integrated English route unavailable") from None
    except (URLError, OSError, TimeoutError):
        raise NativeRPHUnavailable("Integrated English route unavailable") from None
    if not 0 < len(content) <= limit:
        raise NativeRPHUnavailable("Invalid integrated English response size")
    if fmt == "metadata":
        try:
            pair = json.loads(content)["lessons"]
            if (not isinstance(pair, list) or len(pair) != 2
                    or any(type(n) is not int or not 1 <= n <= 160 for n in pair)
                    or pair[1] != pair[0] + 1 or data["lesson"] not in pair):
                raise ValueError("Invalid integrated lesson identity")
            return pair
        except (KeyError, TypeError, ValueError):
            raise NativeRPHUnavailable("Invalid integrated lesson identity") from None
    import io
    from zipfile import BadZipFile, ZipFile
    if fmt == "pdf":
        if not content.startswith(b"%PDF-") or len(content) < 1000:
            raise NativeRPHUnavailable("Invalid integrated English PDF")
    else:
        try:
            with ZipFile(io.BytesIO(content)) as doc:
                if "word/document.xml" not in doc.namelist() or doc.testzip():
                    raise ValueError("Invalid integrated English Word")
        except (BadZipFile, ValueError):
            raise NativeRPHUnavailable("Invalid integrated English Word") from None
    return io.BytesIO(content)
