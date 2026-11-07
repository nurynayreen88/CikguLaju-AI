"""Production-safe shared Google OAuth PKCE state and verified email checks.
No staging project, payment store or environment flags imported here.
"""
import hashlib
import hmac
import time

STATE_TTL = 300

def _seal_state(verifier, state, issued_at, secret):
    body = f"{verifier}.{state}.{issued_at}"
    mac = hmac.new(secret.encode(), body.encode("ascii"), hashlib.sha256).hexdigest()
    return body + "." + mac


def _unseal_state(cookie, secret):
    if not isinstance(cookie, str) or len(cookie) > 400:
        return None
    parts = cookie.split(".")
    if len(parts) != 4:
        return None
    verifier, state, issued, supplied = parts
    if (len(verifier) < 43 or len(verifier) > 128
            or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in verifier)
            or len(state) != 32 or any(c not in "0123456789abcdef" for c in state)
            or len(supplied) != 64 or any(c not in "0123456789abcdef" for c in supplied)):
        return None
    try:
        when = int(issued)
    except ValueError:
        return None
    now = int(time.time())
    if when <= 0 or when > now or now - when > STATE_TTL or str(when) != issued:
        return None
    body = ".".join(parts[:-1])
    expected = hmac.new(secret.encode(), body.encode("ascii"), hashlib.sha256).hexdigest()
    return (verifier, state) if hmac.compare_digest(expected, supplied) else None

def verified_google_email(auth_user):
    """Only a confirmed email on the server-fetched Supabase Google user.

    The email is a login identifier, NOT proof of an existing Telegram account
    or any paid entitlement. Google subject UUID remains the OAuth binding.
    """
    import re
    if not isinstance(auth_user, dict) or not auth_user.get("email_confirmed_at"):
        raise ValueError("Unverified Google email")
    providers = auth_user.get("identities")
    if not isinstance(providers, list):
        raise ValueError("Google OAuth identity required")
    # A Supabase account can have several providers. The verified email for
    # this login MUST be the email of the Google provider itself, not an email
    # address attached to a different (possibly linked) provider.
    google_emails = []
    for identity in providers:
        if isinstance(identity, dict) and identity.get("provider") == "google":
            data = identity.get("identity_data")
            if not isinstance(data, dict) or not isinstance(data.get("email"), str):
                raise ValueError("Google provider email unconfirmed")
            google_emails.append(data["email"].lower())
    if len(google_emails) != 1:
        raise ValueError("Unique Google OAuth identity required")
    email = auth_user.get("email")
    if not isinstance(email, str) or email != email.strip():
        raise ValueError("Invalid Google email")
    email = email.lower()
    if google_emails[0] != email:
        raise ValueError("Google provider email differs from login email")
    if (len(email) > 254 or not re.fullmatch(
        r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+", email
    )):
        raise ValueError("Invalid verified login email")
    return email
