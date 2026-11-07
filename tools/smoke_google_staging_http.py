"""Non-credentialed HTTP acceptance smoke for CikguLaju *staging only*.

Run from a GitHub-hosted runner AFTER staging Google feature flag is enabled.
Never follows the Google provider redirect and never uses a real user session.
"""
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler


BASE = "https://cikgulaju-google-payments-staging.onrender.com"
SUPABASE = "eqrcjlnvcytkgazptbor.supabase.co"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, _request, _fp, _code, _msg, _headers, _newurl):
        return None


opener = build_opener(NoRedirect())


def fetch(path):
    req = Request(BASE + path, headers={
        "Accept": "application/json" if path.startswith("/api") or path.endswith("z")
        else "text/html",
        "User-Agent": "CikguLaju-Staging-Smoke/1",
    })
    try:
        with opener.open(req, timeout=25) as reply:
            return reply.status, reply.headers, reply.read(4096)
    except HTTPError as exc:
        return exc.code, exc.headers, exc.read(4096)


def check():
    status, _headers, blob = fetch("/healthz")
    assert status == 200, ("healthz", status)
    health = json.loads(blob)
    assert health.get("service") == "cikgulaju-google-payments-staging", "wrong service"

    status, _headers, blob = fetch("/readyz")
    assert status == 200, ("readyz not Google-ready; keep production untouched", status)
    ready = json.loads(blob)
    assert ready.get("google_login_configured") is True, "Google config not ready"
    assert ready.get("rph_generator_enabled") is False, "RPH staging gate unexpectedly open"
    assert ready.get("real_payments_enabled") is False, "Real payment gate unexpectedly open"
    assert ready.get("rph_staging_test_gate_open") is False, (
        "Google native RPH staging generation should remain disabled")
    native_configured = ready.get("native_renderer_credentials_configured")
    assert type(native_configured) is bool, "Missing safe private bridge diagnostic"
    print("PASS: native RPH bridge credentials configured:",
          native_configured, "; generation gate remains off.")

    status, headers, blob = fetch("/google-staging-login")
    assert status == 200 and b"/api/auth/google/start" in blob, ("login page", status)
    assert "no-store" in headers.get("Cache-Control", "no-store"), "cache-policy"

    status, _headers, _body = fetch("/api/auth/google/status")
    assert status == 401, ("anonymous Google status should fail", status)

    status, headers, _body = fetch("/google-staging-account")
    assert status == 303, ("anonymous profile page should redirect", status)
    assert headers.get("Location") == "/google-staging-login", "bad anonymous redirect"

    status, headers, _body = fetch("/api/auth/google/profile")
    assert status == 401, ("anonymous profile API should fail", status)

    # Newly mounted Web lesson selector must never expose curriculum
    # metadata without a valid Google-only signed session.
    status, headers, _body = fetch("/google-staging-web")
    assert status == 303, ("anonymous Web selector page", status)
    assert headers.get("Location") == "/google-staging-login", "selector login gate"

    for endpoint in (
        "/api/google-staging/web/catalog",
        "/api/google-staging/web/catalog?year=3&subject=ENGLISH",
        "/api/google-staging/web/materials?year=3&subject=ENGLISH&component=&unit=One&lesson=e-3-001",
        "/api/google-staging/web/rph/recent",
        "/api/google-staging/web/rph/jobs/0ebc954f-85e1-4c06-b4d2-41a8bf811111/download/pdf",
    ):
        status, _headers, _body = fetch(endpoint)
        assert status == 401, ("anonymous Web lesson metadata must fail", endpoint, status)

    status, headers, _body = fetch("/api/auth/google/start")
    assert status == 302, ("OAuth start", status)
    target = urlsplit(headers.get("Location", ""))
    assert target.scheme == "https" and target.hostname == SUPABASE, "wrong project redirect"
    assert target.path == "/auth/v1/authorize", "wrong provider endpoint"
    params = parse_qs(target.query)
    assert params.get("provider") == ["google"], "wrong OAuth provider"
    assert params.get("code_challenge_method") == ["s256"], "PKCE missing"
    assert params.get("code_challenge"), "no PKCE challenge"
    state_cookie = headers.get("Set-Cookie", "")
    assert "cikgulaju_google_oauth_staging_state=" in state_cookie, "no OAuth state"
    assert "Secure" in state_cookie and "HttpOnly" in state_cookie, "insecure OAuth cookie"

    # Follow only the first, public redirect into *staging Supabase Auth*.
    # Do NOT follow the resulting Google provider redirect or submit credentials.
    auth_request = Request(target.geturl(), headers={
        "Accept": "text/html", "User-Agent": "CikguLaju-Staging-Smoke/1",
    })
    try:
        with opener.open(auth_request, timeout=25) as provider:
            provider_status, provider_headers = provider.status, provider.headers
    except HTTPError as exc:
        provider_status, provider_headers = exc.code, exc.headers
    assert provider_status in (302, 303, 307), (
        "staging Supabase Google provider not redirecting", provider_status)
    google_target = urlsplit(provider_headers.get("Location", ""))
    assert google_target.scheme == "https" and google_target.hostname == "accounts.google.com", (
        "Google provider unavailable or wrong destination", google_target.hostname)
    print("PASS: staging endpoint, login security, PKCE redirect and enabled Google provider; no user login performed.")


if __name__ == "__main__":
    try:
        check()
    except (AssertionError, HTTPError, URLError, ValueError, KeyError) as exc:
        print("FAIL: isolated staging HTTP smoke:", str(exc), file=sys.stderr)
        sys.exit(1)
