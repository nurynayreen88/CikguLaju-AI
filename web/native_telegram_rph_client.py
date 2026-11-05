"""Authenticated server-to-server Web proxy for Telegram's REAL RPH engine.

The public Web already checks signed Telegram session, approved lesson source
and paid account before calling this client. Only the server sends the trusted
source-backed layout over HTTPS. No direct caller ID, trial debit or fallback
to a second, divergent Web document renderer.
"""
import io
import json
import os
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPSHandler
from urllib.error import HTTPError, URLError
from zipfile import ZipFile, BadZipFile

MIMES = {
    "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}
MAX_DOCUMENT=15*1024*1024


class NativeRPHUnavailable(Exception):
    pass


class BlockRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_native_rph(data, fmt, *, opener=None):
    if fmt not in MIMES:
        raise ValueError("Unsupported format")
    base=os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL","").strip()
    token=os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN","")
    parts=urlsplit(base)
    if (parts.scheme!="https" or not parts.hostname or parts.port is not None
        or parts.username or parts.password or parts.path not in ("","/")
        or parts.query or parts.fragment or len(token)<32):
        raise NativeRPHUnavailable("Telegram RPH source not configured")
    if not isinstance(data,dict) or data.get("source")!="existing-standalone-rph":
        raise NativeRPHUnavailable("Unknown RPH source")
    layout=data.get("telegram_layout")
    if not isinstance(layout,dict) or layout.get("style")!="telegram-native-rph-v1":
        raise NativeRPHUnavailable("Telegram RPH layout unavailable")
    body={
        "subject":data["subject"],
        "component":(data["selection"].split("-")[2] if data["subject"]=="PJPK" else None),
        "year":data["year"],
        "lesson":data["lesson"],
        "unit":data["unit"],
        "teacher":data["teacher"],
        "layout":layout,
        "format":fmt,
    }
    raw=json.dumps(body,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    if len(raw)>100000:
        raise NativeRPHUnavailable("RPH source exceeds safe limit")
    url=base.rstrip("/")+"/internal/rph/v1/render"
    req=Request(url,data=raw,headers={
        "Authorization":"Bearer "+token,
        "Content-Type":"application/json",
        "Accept":MIMES[fmt],
    },method="POST")
    transport=opener or build_opener(HTTPSHandler(),BlockRedirects())
    try:
        with transport.open(req,timeout=35) as response:
            if response.status!=200:
                raise NativeRPHUnavailable("Telegram generator not ready")
            mime=response.headers.get("Content-Type","").split(";")[0].strip().lower()
            if mime!=MIMES[fmt]:
                raise NativeRPHUnavailable("Unexpected Telegram document type")
            content=response.read(MAX_DOCUMENT+1)
    except (HTTPError,URLError,OSError,TimeoutError):
        # Do not expose server-to-server URLs, authentication tokens or content.
        raise NativeRPHUnavailable("Telegram document generator unavailable") from None
    if not 1000<=len(content)<=MAX_DOCUMENT:
        raise NativeRPHUnavailable("Invalid native RPH file length")
    if fmt=="pdf":
        if not content.startswith(b"%PDF-"):
            raise NativeRPHUnavailable("Invalid native PDF file")
    else:
        if not content.startswith(b"PK\x03\x04"):
            raise NativeRPHUnavailable("Invalid native Word file")
        try:
            with ZipFile(io.BytesIO(content)) as document:
                if document.testzip() or "word/document.xml" not in document.namelist():
                    raise NativeRPHUnavailable("Corrupt native Word file")
        except (OSError,ValueError,BadZipFile):
            raise NativeRPHUnavailable("Invalid native Word file") from None
    return io.BytesIO(content)
