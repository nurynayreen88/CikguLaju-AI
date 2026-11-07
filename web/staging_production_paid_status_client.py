"""Isolated staging -> production status bridge, read-only and opt-in.

A dedicated strong server-side token is required in BOTH Render services.
Production endpoint is fixed; no browser-originated URL/UID is accepted.
The linked Telegram UID comes from the staging verified identity mapping.
Never write production or staging entitlement rows or spend trial credits.
"""
from datetime import datetime, timezone
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPSHandler

PROD_URL = "https://cikgulaju-web.onrender.com/internal/identity/v1/entitlements"
SOURCE = "cikgulaju-prod-entitlements-v1"
STAGING_URL = "https://eqrcjlnvcytkgazptbor.supabase.co"
MAX_RESPONSE = 2048
COLD_START_TIMEOUT = 55  # Render free Web can require >20 s to wake.
GATEWAY_RETRY_TIMEOUT = 25
GATEWAY_RETRY_BACKOFF = 2


class PaidStatusBridgeUnavailable(RuntimeError):
    pass


class PaidStatusProductionAccountMissing(PaidStatusBridgeUnavailable):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _enabled(cfg):
    token = os.environ.get("CIKGULAJU_PAID_BRIDGE_TOKEN", "")
    return (os.environ.get("CIKGULAJU_PAID_BRIDGE_STAGING_READ_ENABLED") == "1"
            and isinstance(token, str) and len(token) >= 48
            and isinstance(cfg, dict)
            and cfg.get("supabase_url", "").rstrip("/") == STAGING_URL
            and cfg.get("host") == "cikgulaju-google-payments-staging.onrender.com")


def read_paid_status(telegram_uid, cfg, *, transport=None, now=None):
    """A trusted linked ID is checked against one fixed production host only."""
    if not _enabled(cfg):
        raise PaidStatusBridgeUnavailable("Private production status bridge is disabled")
    if type(telegram_uid) is not int or not 0 < telegram_uid <= 9223372036854775807:
        raise ValueError("Verified linked Telegram ID required")
    data = json.dumps({"telegram_user_id": telegram_uid}, separators=(",", ":")).encode("ascii")
    req = Request(PROD_URL, data=data, method="POST",
                  headers={"Authorization": "Bearer " + os.environ["CIKGULAJU_PAID_BRIDGE_TOKEN"],
                           "Accept": "application/json",
                           "Content-Type": "application/json"})
    try:
        opener = transport or build_opener(HTTPSHandler(), NoRedirects())
        def read_response(seconds):
            with opener.open(req, timeout=seconds) as res:
                raw = res.read(MAX_RESPONSE + 1)
                if res.status != 200 or len(raw) > MAX_RESPONSE:
                    raise PaidStatusBridgeUnavailable("Invalid production status reply")
                return raw

        try:
            raw = read_response(COLD_START_TIMEOUT)
        except HTTPError as exc:
            # Render's free Web proxy may reply 502/503 while its WSGI
            # instance wakes. A single read-only retry is safe; 401/403/404
            # MUST NOT be retried as they indicate auth/account failure.
            if exc.code not in (502, 503, 504):
                raise
            time.sleep(GATEWAY_RETRY_BACKOFF)
            raw = read_response(GATEWAY_RETRY_TIMEOUT)
        payload = json.loads(raw)
        if (not isinstance(payload, dict)
                or set(payload) != {"source", "telegram_user_id", "registered",
                                    "rakan_pembangun_active", "subscription_active",
                                    "subscription_expires_at"}
                or payload["source"] != SOURCE
                or type(payload["telegram_user_id"]) is not int
                or payload["telegram_user_id"] != telegram_uid
                or payload["registered"] is not True
                or type(payload["rakan_pembangun_active"]) is not bool
                or type(payload["subscription_active"]) is not bool):
            raise PaidStatusBridgeUnavailable("Unverified production status")
        expiry = payload["subscription_expires_at"]
        if expiry is None:
            if payload["subscription_active"]:
                raise PaidStatusBridgeUnavailable("Active subscription missing expiry")
        else:
            if not isinstance(expiry, str) or len(expiry) > 50:
                raise PaidStatusBridgeUnavailable("Invalid production expiry")
            when = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            if when.tzinfo is None or when <= (now or datetime.now(timezone.utc)):
                raise PaidStatusBridgeUnavailable("Expired or untrusted subscription")
            if payload["subscription_active"] is not True:
                raise PaidStatusBridgeUnavailable("Unexpected inactive subscription expiry")
        return {
            "rakan_pembangun_active": payload["rakan_pembangun_active"],
            "subscription_active": payload["subscription_active"],
            "subscription_expires_at": expiry,
        }
    except HTTPError as exc:
        if exc.code == 404:
            raise PaidStatusProductionAccountMissing("Production account not found") from None
        raise PaidStatusBridgeUnavailable("private_bridge_http_" + str(exc.code)) from None
    except (URLError, OSError, TimeoutError, ValueError, TypeError, KeyError):
        raise PaidStatusBridgeUnavailable("Production status source unavailable") from None


def verified_linked_paid_status(actor, cfg):
    """Status only, not a grant, and never a fallback to staging paid access."""
    from web.provider_neutral_web_identity import canonical_staging_account
    from web.google_telegram_link_staging_routes import (
        _link_status, StagingLinkUnavailable)
    account_id = canonical_staging_account(actor)
    if not _enabled(cfg):
        return {"production_access_status": "bridge_disabled",
                "production_access_verified": False}
    try:
        mapping = _link_status(cfg, account_id)
        if not mapping.get("linked"):
            return {"production_access_status": "not_linked",
                    "production_access_verified": False}
        raw_uid = mapping.get("telegram_user_id")
        if (not isinstance(raw_uid, str) or not raw_uid.isascii()
                or not raw_uid.isdecimal() or raw_uid.startswith("0")
                or not 0 < int(raw_uid) <= 9223372036854775807):
            raise PaidStatusBridgeUnavailable("Invalid linked identity")
        uid = int(raw_uid)
        if actor.provider == "telegram" and actor.subject != raw_uid:
            raise PaidStatusBridgeUnavailable("Mismatched verified Telegram subject")
        found = read_paid_status(uid, cfg)
        return {"production_access_status": "verified",
                "production_access_verified": True,
                "production_rakan_pembangun_active": found["rakan_pembangun_active"],
                "production_subscription_active": found["subscription_active"],
                "production_subscription_expires_at": found["subscription_expires_at"]}
    except PaidStatusProductionAccountMissing:
        return {"production_access_status": "production_account_missing",
                "production_access_verified": False}
    except (PaidStatusBridgeUnavailable, StagingLinkUnavailable,
            ValueError, TypeError, KeyError):
        return {"production_access_status": "source_unavailable",
                "production_access_verified": False}


def verified_paid_uid_for_rph(actor, cfg):
    """Return a verified Telegram UID only for CURRENT production paid access.

    Only called by the staging RPH server from a signed Google/Telegram actor.
    Re-check production per request and immediately before the atomic finish.
    An offline/invalid source must never silently spend trial credits or grant
    paid access. No browser flags, payments, or stale cached entitlements.
    """
    from web.provider_neutral_web_identity import canonical_staging_account
    from web.google_telegram_link_staging_routes import (
        _link_status, StagingLinkUnavailable)

    account_id = canonical_staging_account(actor)
    if not _enabled(cfg):
        raise PaidStatusBridgeUnavailable("Private production status bridge disabled")
    try:
        mapping = _link_status(cfg, account_id)
    except (StagingLinkUnavailable, KeyError, ValueError, TypeError):
        raise PaidStatusBridgeUnavailable("Linked account verification unavailable") from None
    if not isinstance(mapping, dict) or mapping.get("staging_only") is not True:
        raise PaidStatusBridgeUnavailable("Invalid staging linked-account result")
    if mapping.get("linked") is False:
        return None
    if mapping.get("linked") is not True:
        raise PaidStatusBridgeUnavailable("Unverified account linkage")
    raw_uid = mapping.get("telegram_user_id")
    if (not isinstance(raw_uid, str) or not raw_uid.isascii()
            or not raw_uid.isdecimal() or raw_uid.startswith("0")
            or not 0 < int(raw_uid) <= 9223372036854775807):
        raise PaidStatusBridgeUnavailable("Unverified Telegram ID")
    if actor.provider == "telegram" and actor.subject != raw_uid:
        raise PaidStatusBridgeUnavailable("Telegram session subject mismatch")
    uid = int(raw_uid)
    try:
        paid = read_paid_status(uid, cfg)
    except PaidStatusProductionAccountMissing:
        # A verified link to an unknown production user is NOT a paid grant.
        return None
    if (type(paid.get("rakan_pembangun_active")) is not bool
            or type(paid.get("subscription_active")) is not bool):
        raise PaidStatusBridgeUnavailable("Incomplete production entitlement status")
    return uid if (paid["rakan_pembangun_active"] or paid["subscription_active"]) else None
