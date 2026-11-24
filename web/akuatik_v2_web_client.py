"""Exact existing-PdP Aquatics V2 proxy. Original lesson IDs remain unchanged."""
import io, json, os
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPSHandler
from urllib.error import HTTPError, URLError
from zipfile import ZipFile, BadZipFile
from web.native_telegram_rph_client import MIMES, MAX_DOCUMENT, BlockRedirects, NativeRPHUnavailable

KSSR={(3,22):"022",(3,23):"023",(4,26):"026"}
KP2027={("A",51):"KP2027-A-051",("B",50):"KP2027-B-050"}
def kssr_id(year,subject,component,token):
    if subject!="PJPK" or component!="PJ":
        return None
    for (y,n),key in KSSR.items():
        if year==y and token==f"p-{y}-PJ-{n:03d}":
            return key
    return None

def request_document(year,source_id,fmt,teacher,*,opener=None):
    if fmt not in MIMES or (year,source_id) not in {
        (3,"022"),(3,"023"),(4,"026"),(1,"KP2027-A-051"),(1,"KP2027-B-050")}:
        raise ValueError("Invalid V2 selection")
    base=os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL","").strip()
    token=os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN","")
    parts=urlsplit(base)
    if (parts.scheme!="https" or not parts.hostname or parts.port is not None
        or parts.username or parts.password or parts.path not in ("","/")
        or parts.query or parts.fragment or len(token)<32):
        raise NativeRPHUnavailable("Aquatics source not configured")
    payload={"year":year,"source_id":source_id,"format":fmt,
             "teacher":{k:str(teacher.get(k) or "") for k in ("class","date","time","students")}}
    req=Request(base.rstrip("/")+"/internal/rph/v1/akuatik-v2/render",
        data=json.dumps(payload).encode(),method="POST",headers={
            "Authorization":"Bearer "+token,"Content-Type":"application/json","Accept":MIMES[fmt]})
    transport=opener or build_opener(HTTPSHandler(),BlockRedirects())
    try:
        with transport.open(req,timeout=35) as response:
            if response.status!=200 or response.headers.get("Content-Type","").split(";")[0].strip().lower()!=MIMES[fmt]:
                raise NativeRPHUnavailable("Aquatics V2 unavailable")
            content=response.read(MAX_DOCUMENT+1)
    except (HTTPError,URLError,OSError,TimeoutError):
        raise NativeRPHUnavailable("Aquatics V2 unavailable") from None
    if not 1000<=len(content)<=MAX_DOCUMENT or not content.startswith(b"%PDF-" if fmt=="pdf" else b"PK\x03\x04"):
        raise NativeRPHUnavailable("Invalid document")
    if fmt=="word":
        try:
            with ZipFile(io.BytesIO(content)) as z:
                if z.testzip() or "word/document.xml" not in z.namelist():
                    raise NativeRPHUnavailable("Invalid Word document")
        except (OSError,ValueError,BadZipFile):
            raise NativeRPHUnavailable("Invalid Word document") from None
    return io.BytesIO(content)
