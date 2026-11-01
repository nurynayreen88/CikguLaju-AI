"""Browser-bound proof for the isolated QR pairing flow.

The QR challenge is NOT proof that a desktop browser owns the pending login.
This module issues a separate, random browser secret and verifies its HMAC
binding to the challenge hash. Never put browser_secret in a QR or bot message.
No HTTP routes, cookies, or production integration are enabled here.
"""
import hashlib
import hmac
import secrets


def create_browser_binding(challenge_hash, signing_secret):
    if not isinstance(challenge_hash, str) or len(challenge_hash) != 64:
        raise ValueError("invalid challenge hash")
    if not isinstance(signing_secret, str) or len(signing_secret) < 32:
        raise ValueError("invalid signing secret")
    browser_secret = secrets.token_urlsafe(32)
    payload = f"web-v1-pairing:{challenge_hash}:{browser_secret}".encode("ascii")
    signature = hmac.new(signing_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return browser_secret, signature


def verify_browser_binding(challenge_hash, browser_secret, signature, signing_secret):
    if not isinstance(challenge_hash, str) or len(challenge_hash) != 64:
        return False
    if not isinstance(browser_secret, str) or not 40 <= len(browser_secret) <= 64:
        return False
    if any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in browser_secret):
        return False
    if not isinstance(signature, str) or len(signature) != 64:
        return False
    if any(c not in "0123456789abcdef" for c in signature):
        return False
    if not isinstance(signing_secret, str) or len(signing_secret) < 32:
        return False
    payload = f"web-v1-pairing:{challenge_hash}:{browser_secret}".encode("ascii")
    expected = hmac.new(signing_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
