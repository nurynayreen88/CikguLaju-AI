"""Uncredentialed check: production paid-status route must be private.

No actual Telegram ID, user session, payment detail or secret is sent.
This checks that the approved production Web API is mounted and its
private bearer guard is enabled; it does NOT grant or test paid access.
"""
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL="https://cikgulaju-web.onrender.com/internal/identity/v1/entitlements"
req=Request(URL, method="POST",
    data=json.dumps({"telegram_user_id":9223372036854775807}).encode("utf-8"),
    headers={"Content-Type":"application/json","Accept":"application/json"})
try:
    with urlopen(req,timeout=65) as response:
        status=response.status
except HTTPError as exc:
    status=exc.code
except (URLError,OSError,TimeoutError) as exc:
    print("Production paid bridge inaccessible:",type(exc).__name__)
    sys.exit(1)
print("Production paid bridge unauthenticated HTTP status:",status)
assert status == 401, "Private API is not enabled or its bearer guard is not active"
