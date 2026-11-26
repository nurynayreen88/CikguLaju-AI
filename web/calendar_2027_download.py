"""Exact owner-approved A2 calendar. Fixed private object; no arbitrary upload."""
from hashlib import sha256
from io import BytesIO
from urllib.request import Request,build_opener
from urllib.error import HTTPError,URLError
from flask import jsonify,request,send_file
from web.rpt_kssr_bm_private_storage import _server_settings,NoRedirects,PrivateWordUnavailable,BUCKET
from web.admin_usage_web import allowed_admin_ids

SHA="546b580c564ef15a7d8b30bb6f27d58be964f001fcb37b24af604248b21088df"
SIZE=158569
KEY="calendar/2027/CikguLaju_Kalendar_2027_A2_Kemas.pdf"
NAME="CikguLaju_Kalendar_2027_A2_Kemas.pdf"

def valid(blob):
    return len(blob)==SIZE and blob.startswith(b"%PDF-") and sha256(blob).hexdigest()==SHA

def storage_request(config,method,blob=None):
    base,key=_server_settings(config)
    headers={"apikey":key,"Accept":"application/pdf"}
    if not key.startswith("sb_secret_"):
        headers["Authorization"]="Bearer "+key
    prefix="authenticated/" if method=="GET" else ""
    if method=="POST":
        headers.update({"Content-Type":"application/pdf","x-upsert":"false"})
    return build_opener(NoRedirects()).open(Request(
        f"{base}/storage/v1/object/{prefix}{BUCKET}/{KEY}",
        data=blob,headers=headers,method=method),timeout=12)

def read(config):
    try:
        with storage_request(config,"GET") as response:
            blob=response.read(SIZE+1)
        return blob if valid(blob) else None
    except (PrivateWordUnavailable,HTTPError,URLError,OSError,ValueError):
        return None

def install_routes(bp,account_lookup):
    from web_v1_telegram_auth_routes import _config
    def is_admin(account):
        return account.get("telegram_user_id") in allowed_admin_ids()

    @bp.get("/api/rpt/2027/calendar/status")
    def calendar_status():
        account,error=account_lookup()
        if error is not None:return error
        return jsonify({"ready":read(_config()) is not None,"admin":is_admin(account)})

    @bp.get("/api/rpt/2027/calendar.pdf")
    def calendar_download():
        account,error=account_lookup()
        if error is not None:return error
        blob=read(_config())
        if blob is None:return jsonify({"error":"Kalendar belum tersedia."}),503
        response=send_file(BytesIO(blob),mimetype="application/pdf",as_attachment=True,download_name=NAME,conditional=False)
        response.headers["X-Calendar-SHA256"]=SHA
        return response

    @bp.post("/api/rpt/2027/calendar/upload")
    def calendar_upload():
        account,error=account_lookup()
        if error is not None:return error
        if not is_admin(account):return jsonify({"error":"Akses admin diperlukan."}),403
        if (request.headers.get("Origin")!="https://"+request.host
                or request.mimetype!="application/pdf" or request.content_length!=SIZE):
            return jsonify({"error":"Pilih PDF A2 versi Kemas yang asal."}),400
        blob=request.get_data(cache=False)
        if not valid(blob):return jsonify({"error":"Fail tidak sepadan dengan PDF yang diluluskan."}),400
        config=_config()
        if read(config) is None:
            try:
                with storage_request(config,"POST",blob) as response:
                    response.read(4096)
            except (PrivateWordUnavailable,HTTPError,URLError,OSError,ValueError):
                # Retry read: a duplicate upload may already have succeeded.
                pass
        if read(config) is None:return jsonify({"error":"Storan belum mengesahkan fail. Cuba semula."}),503
        return jsonify({"ready":True})
