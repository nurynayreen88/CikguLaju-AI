"""Private two-way CikguLaju user/admin support chat."""
import json
import re
import uuid
from urllib.parse import urlsplit
from urllib.parse import urlencode
from urllib.request import Request, HTTPSHandler, build_opener
from urllib.error import HTTPError, URLError
from flask import Blueprint, Response, jsonify, request
from web.teacher_profile_routes import _auth
from web.admin_usage_web import allowed_admin_ids
from web.teacher_profile_store import NoRedirect

bp=Blueprint("web_admin_chat",__name__)
MAX_REPLY=120000
MAX_FILE=4*1024*1024
MIME={"application/pdf":"pdf","image/png":"png","image/jpeg":"jpg","image/webp":"webp"}
BUCKET="cikgulaju-materials"

@bp.after_request
def protect(resp):
    resp.headers["Cache-Control"]="no-store, private"
    resp.headers["Vary"]="Cookie"
    resp.headers["X-Content-Type-Options"]="nosniff"
    return resp

def _valid_id(raw):
    return (isinstance(raw,str) and bool(re.fullmatch(r"[1-9][0-9]{0,18}",raw))
            and int(raw)<2**63)

def _db(conf,method,params=None,body=None):
    base=conf["supabase_url"].rstrip("/")
    key=conf["supabase_key"]
    if not base.startswith("https://") or len(key)<20:
        raise ValueError("Backend not configured")
    url=base+"/rest/v1/web_admin_chat_messages"
    if params:url+="?"+urlencode(params)
    headers={"apikey":key,"Content-Type":"application/json","Accept":"application/json"}
    if not key.startswith("sb_secret_"):headers["Authorization"]="Bearer "+key
    if body is not None:headers["Prefer"]="return=representation"
    raw=json.dumps(body).encode() if body is not None else None
    req=Request(url,method=method,data=raw,headers=headers)
    with build_opener(HTTPSHandler(),NoRedirect()).open(req,timeout=7) as resp:
        if resp.status not in (200,201):raise ValueError("Unexpected response")
        payload=resp.read(MAX_REPLY+1)
    if len(payload)>MAX_REPLY:raise ValueError("Response too large")
    result=json.loads(payload)
    if not isinstance(result,list):raise ValueError("Unexpected records")
    return result

def _storage(conf,method,path,raw=None,mime=None):
    """Never use public URLs or accept browser-chosen storage paths."""
    base=conf["supabase_url"].rstrip("/")
    parsed=urlsplit(base)
    if parsed.scheme!="https" or not parsed.hostname or parsed.port or parsed.username or parsed.password or parsed.path not in ("","/"):
        raise ValueError("Invalid storage host")
    key=conf["supabase_key"]
    if not isinstance(key,str) or len(key)<20:raise ValueError("Missing storage key")
    if not re.fullmatch(r"chat/[0-9]{1,19}/[0-9a-f]{32}\.(pdf|png|jpg|webp)",path):
        raise ValueError("Invalid storage key")
    headers={"apikey":key, "Cache-Control":"no-store"}
    if not key.startswith("sb_secret_"):headers["Authorization"]="Bearer "+key
    if method=="POST":
        url=base+"/storage/v1/object/"+BUCKET+"/"+path
        headers["Content-Type"]=mime
        headers["x-upsert"]="false"
    elif method=="GET":
        # Private buckets require authenticated endpoint, never public URL.
        url=base+"/storage/v1/object/authenticated/"+BUCKET+"/"+path
    else:
        raise ValueError("Unsupported storage operation")
    req=Request(url,data=raw if method=="POST" else None,method=method,headers=headers)
    with build_opener(HTTPSHandler(),NoRedirect()).open(req,timeout=15) as resp:
        if resp.status not in (200,201,204):raise ValueError("Storage request failed")
        content=resp.read((MAX_FILE+1) if method=="GET" else 1024)
        if method=="GET" and len(content)>MAX_FILE:raise ValueError("Stored attachment exceeds limit")
    return content


def _message_with_attachment(conf,uid,owner,role):
    """Single optional attachment per message; user cannot choose owner."""
    if not _origin_ok() or not request.content_length or request.content_length>MAX_FILE+16000:
        return None
    if request.mimetype=="application/json":
        message=_clean_message()
        return {"user_id":owner,"sender_id":uid,"sender_role":role,"message":message} if message else None
    if request.mimetype!="multipart/form-data" or set(request.form)!={"message"} or set(request.files)!={"file"}:
        return None
    message=request.form.get("message","").strip()
    if len(message)>1500:return None
    upload=request.files["file"]
    mime=upload.mimetype
    content=upload.stream.read(MAX_FILE+1)
    if mime not in MIME or not 700<=len(content)<=MAX_FILE:return None
    signatures={"application/pdf":content.startswith(b"%PDF-"),
                "image/png":content.startswith(b"\x89PNG\r\n\x1a\n"),
                "image/jpeg":content.startswith(b"\xff\xd8\xff"),
                "image/webp":content.startswith(b"RIFF") and content[8:12]==b"WEBP"}
    if not signatures[mime]:return None
    extension=MIME[mime]
    path=f"chat/{owner}/{uuid.uuid4().hex}.{extension}"
    name=(upload.filename or "lampiran").rsplit("/",1)[-1].rsplit("\\\\",1)[-1]
    name=re.sub(r"[^A-Za-z0-9 ._()-]","_",name)[:100] or "lampiran"
    _storage(conf,"POST",path,content,mime)
    return {"user_id":owner,"sender_id":uid,"sender_role":role,
            "message":message or "📎 Lampiran", "attachment_path":path,
            "attachment_name":name,"attachment_mime":mime,"attachment_size":len(content)}


def _public_rows(rows):
    return [{"id":r["id"],"sender_role":r["sender_role"],"message":r["message"],
             "created_at":r["created_at"],
             "attachment_name":r.get("attachment_name") if r.get("attachment_path") else None}
            for r in rows]


def _attachment(conf,uid,message_id,admin=False):
    params={"select":"user_id,attachment_path,attachment_mime,attachment_name",
            "id":"eq."+str(message_id),"limit":"1"}
    if not admin:params["user_id"]="eq."+str(uid)
    rows=_db(conf,"GET",params)
    if not rows or not rows[0].get("attachment_path"):
        return jsonify({"error":"Lampiran tidak dijumpai"}),404
    row=rows[0]
    content=_storage(conf,"GET",row["attachment_path"])
    mime=row["attachment_mime"]
    if mime not in MIME or len(content)>MAX_FILE:raise ValueError("Invalid stored attachment")
    response=Response(content,mimetype=mime)
    response.headers["Content-Disposition"]="attachment; filename=lampiran."+MIME[mime]
    response.headers["Content-Security-Policy"]="sandbox; default-src 'none'"
    response.headers["Cross-Origin-Resource-Policy"]="same-origin"
    return response


def _origin_ok():
    return request.headers.get("Origin")=="https://"+request.host

def _clean_message():
    if not _origin_ok() or not request.is_json or not request.content_length or request.content_length>4000:
        return None
    data=request.get_json(silent=True)
    if not isinstance(data,dict) or set(data)!={"message"} or not isinstance(data["message"],str):
        return None
    message=data["message"].strip()
    if not 1<=len(message)<=1500:return None
    return message

@bp.get("/api/web/chat")
def own_chat():
    conf,uid,err=_auth()
    if err is not None:return err
    try:
        rows=_db(conf,"GET",{"select":"id,sender_role,message,created_at,attachment_path,attachment_name",
             "user_id":"eq."+str(uid),"order":"id.desc","limit":"100"})
        return jsonify({"items":_public_rows(list(reversed(rows)))})
    except (ValueError,KeyError,TypeError,OSError,HTTPError,URLError):
        return jsonify({"error":"Chat belum dapat dimuatkan"}),503

@bp.post("/api/web/chat")
def own_send():
    conf,uid,err=_auth()
    if err is not None:return err
    try:
        payload=_message_with_attachment(conf,uid,uid,"user")
        if payload is None:return jsonify({"error":"Mesej atau lampiran tidak sah (PDF/gambar maksimum 4 MB)"}),400
        rows=_db(conf,"POST",body=payload)
        if len(rows)!=1:raise ValueError("Unconfirmed")
        return jsonify({"sent":True}),201
    except (ValueError,KeyError,TypeError,OSError,HTTPError,URLError):
        return jsonify({"error":"Mesej belum dapat dihantar"}),503

@bp.get("/api/web/admin/chats")
def admin_inbox():
    conf,uid,err=_auth()
    if err is not None:return err
    if uid not in allowed_admin_ids():return jsonify({"error":"Admin sahaja"}),403
    try:
        rows=_db(conf,"GET",{"select":"id,user_id,sender_role,message,created_at",
              "order":"id.desc","limit":"300"})
        seen=set();items=[]
        for row in rows:
            key=str(row["user_id"])
            if key not in seen:
                seen.add(key)
                items.append({"user_id":key,"last_message":row["message"][:100],
                              "created_at":row["created_at"],"sender_role":row["sender_role"]})
        return jsonify({"items":items})
    except (ValueError,KeyError,TypeError,OSError,HTTPError,URLError):
        return jsonify({"error":"Senarai chat belum tersedia"}),503

@bp.get("/api/web/admin/chats/<user_id>")
def admin_thread(user_id):
    conf,uid,err=_auth()
    if err is not None:return err
    if uid not in allowed_admin_ids():return jsonify({"error":"Admin sahaja"}),403
    if not _valid_id(user_id):return jsonify({"error":"ID tidak sah"}),400
    try:
        rows=_db(conf,"GET",{"select":"id,sender_role,message,created_at,attachment_path,attachment_name",
             "user_id":"eq."+user_id,"order":"id.desc","limit":"100"})
        return jsonify({"items":_public_rows(list(reversed(rows))),"user_id":user_id})
    except (ValueError,KeyError,TypeError,OSError,HTTPError,URLError):
        return jsonify({"error":"Perbualan belum tersedia"}),503

@bp.post("/api/web/admin/chats/<user_id>")
def admin_send(user_id):
    conf,uid,err=_auth()
    if err is not None:return err
    if uid not in allowed_admin_ids():return jsonify({"error":"Admin sahaja"}),403
    if not _valid_id(user_id):return jsonify({"error":"ID tidak sah"}),400
    try:
        payload=_message_with_attachment(conf,uid,int(user_id),"admin")
        if payload is None:return jsonify({"error":"Mesej atau lampiran tidak sah (PDF/gambar maksimum 4 MB)"}),400
        rows=_db(conf,"POST",body=payload)
        if len(rows)!=1:raise ValueError("Unconfirmed")
        return jsonify({"sent":True}),201
    except (ValueError,KeyError,TypeError,OSError,HTTPError,URLError):
        return jsonify({"error":"Balasan belum dapat dihantar"}),503

@bp.get("/api/web/chat/attachments/<int:message_id>")
def own_attachment(message_id):
    conf,uid,err=_auth()
    if err is not None:return err
    if message_id<=0:return jsonify({"error":"ID lampiran tidak sah"}),400
    try:return _attachment(conf,uid,message_id)
    except (ValueError,KeyError,TypeError,OSError,HTTPError,URLError):
        return jsonify({"error":"Lampiran belum dapat dibuka"}),503

@bp.get("/api/web/admin/chat-attachments/<int:message_id>")
def admin_attachment(message_id):
    conf,uid,err=_auth()
    if err is not None:return err
    if uid not in allowed_admin_ids():return jsonify({"error":"Admin sahaja"}),403
    if message_id<=0:return jsonify({"error":"ID lampiran tidak sah"}),400
    try:return _attachment(conf,uid,message_id,admin=True)
    except (ValueError,KeyError,TypeError,OSError,HTTPError,URLError):
        return jsonify({"error":"Lampiran belum dapat dibuka"}),503
