"""Public, read-only Web production smoke probe. No tokens or accounts used."""
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

BASE = "https://cikgulaju-web.onrender.com"

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, url):
        return None

client = build_opener(NoRedirect())

def get(path):
    req = Request(BASE+path,headers={"Accept":"application/json","User-Agent":"cikgulaju-production-smoke/1"})
    try:
        with client.open(req,timeout=18) as r:
            code=r.status
            body=r.read(16000)
    except HTTPError as e:
        code=e.code
        body=e.read(16000)
    except URLError as e:
        return None, {"error":"connection_unavailable","reason_type":type(e.reason).__name__}
    try:
        return code,json.loads(body)
    except (ValueError,UnicodeDecodeError):
        return code,{"error":"non_json_response"}

checks = [
    ("/healthz", 200),
    ("/readyz", 200),
    ("/api/auth/capabilities", 200),
    ("/api/source/status", 200),
    ("/api/auth/telegram/session", 401),
    ("/api/options?kind=subjects&year=2", 401),
    ("/api/web/rph/preview", 401),
    ("/api/web/rph/word", 401),
    ("/api/web/teacher/classes", 401),
    ("/api/rpt/2027/catalog", 401),
]

failed=False
for path,expected in checks:
    code,body=get(path)
    ok=code==expected
    if path=="/readyz":
        ok=ok and body.get("ready") is True and body.get("authoritative_curriculum_reachable") is True
    if path=="/api/auth/capabilities":
        ok=ok and body.get("telegram_widget_enabled") is True
    if path=="/api/source/status":
        ok=ok and body.get("shared_source_verified") is True
    # Expose safe booleans only. Never emit response secrets, tokens, URLs or user records.
    safe={}
    if path=="/readyz":
        safe={k:bool(body.get(k)) for k in (
            "ready","account_lookup_configured","authoritative_curriculum_configured",
            "authoritative_curriculum_reachable")}
    if path=="/api/auth/capabilities":
        safe={"telegram_widget_enabled":bool(body.get("telegram_widget_enabled"))}
    if path=="/api/source/status":
        safe={"shared_source_verified":bool(body.get("shared_source_verified"))}
    print(json.dumps({"path":path,"http":code,"expected":expected,"passed":ok,**safe}))
    failed=failed or not ok
print("PUBLIC_WEB_PROBE_PASS" if not failed else "PUBLIC_WEB_PROBE_FAIL")
sys.exit(1 if failed else 0)
