"""Private two-way CikguLaju user/admin support chat."""
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, HTTPSHandler, build_opener
from urllib.error import HTTPError, URLError
from flask import Blueprint, jsonify, request
from web.teacher_profile_routes import _auth
from web.admin_usage_web import allowed_admin_ids
from web.teacher_profile_store import NoRedirect

bp=Blueprint("web_admin_chat",__name__)
MAX_REPLY=120000

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
        rows=_db(conf,"GET",{"select":"id,sender_role,message,created_at",
             "user_id":"eq."+str(uid),"order":"id.desc","limit":"100"})
        return jsonify({"items":list(reversed(rows))})
    except (ValueError,KeyError,TypeError,OSError,HTTPError,URLError):
        return jsonify({"error":"Chat belum dapat dimuatkan"}),503

@bp.post("/api/web/chat")
def own_send():
    conf,uid,err=_auth()
    if err is not None:return err
    message=_clean_message()
    if message is None:return jsonify({"error":"Mesej tidak sah"}),400
    try:
        rows=_db(conf,"POST",body={"user_id":uid,"sender_id":uid,
                    "sender_role":"user","message":message})
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
        rows=_db(conf,"GET",{"select":"id,sender_role,message,created_at",
             "user_id":"eq."+user_id,"order":"id.desc","limit":"100"})
        return jsonify({"items":list(reversed(rows)),"user_id":user_id})
    except (ValueError,KeyError,TypeError,OSError,HTTPError,URLError):
        return jsonify({"error":"Perbualan belum tersedia"}),503

@bp.post("/api/web/admin/chats/<user_id>")
def admin_send(user_id):
    conf,uid,err=_auth()
    if err is not None:return err
    if uid not in allowed_admin_ids():return jsonify({"error":"Admin sahaja"}),403
    if not _valid_id(user_id):return jsonify({"error":"ID tidak sah"}),400
    message=_clean_message()
    if message is None:return jsonify({"error":"Mesej tidak sah"}),400
    try:
        rows=_db(conf,"POST",body={"user_id":int(user_id),"sender_id":uid,
                    "sender_role":"admin","message":message})
        if len(rows)!=1:raise ValueError("Unconfirmed")
        return jsonify({"sent":True}),201
    except (ValueError,KeyError,TypeError,OSError,HTTPError,URLError):
        return jsonify({"error":"Balasan belum dapat dihantar"}),503
