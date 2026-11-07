"""Server-trusted, provider-neutral Web identity (no automatic account linking).

Do not derive authorization from browser-provided email, name, Telegram ID,
or an OAuth display label. Existing Telegram RPH access remains Telegram-only
until a reviewed shared quota/entitlement migration is deployed.
"""
from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class VerifiedWebIdentity:
    provider: str
    subject: str
    account_id: str | None = None

    @property
    def can_use_legacy_telegram_rph(self):
        return self.provider == "telegram" and self.account_id is None

    @property
    def can_use_google_rph(self):
        # Neither a successful Google login nor ten display-only staging
        # credits authorizes RPH generation through the Telegram generator.
        return False


def from_verified_google_account(account_id, profile):
    """Call ONLY after server-side verification of Google signed ticket + DB."""
    try:
        normalized = str(uuid.UUID(account_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Verified Google account UUID required") from None
    if normalized != account_id or not isinstance(profile, dict):
        raise ValueError("Google account must be canonical and trusted")
    if profile.get("account_id") != account_id:
        raise ValueError("Google account DB identity mismatch")
    credits = profile.get("trial_remaining")
    if type(credits) is not int or not 0 <= credits <= 10:
        raise ValueError("Unverified trial credits")
    return VerifiedWebIdentity("google", normalized, normalized)


def from_verified_telegram_account(user_id, account):
    """Existing Telegram HMAC/session and backend account must be confirmed first."""
    if (type(user_id) is not int or user_id <= 0
            or not isinstance(account, dict)
            or account.get("authenticated") is not True
            or account.get("telegram_user_id") != user_id):
        raise ValueError("Verified Telegram account required")
    return VerifiedWebIdentity("telegram", str(user_id))




def from_verified_linked_telegram_account(user_id, account_id, profile):
    """Only after a validated Widget session AND strict staging DB linkage."""
    actor = from_verified_telegram_account(
        user_id, {"authenticated": True, "telegram_user_id": user_id})
    if not isinstance(profile, dict) or profile.get("account_id") != account_id:
        raise ValueError("Staging account profile mismatch")
    credits = profile.get("trial_remaining")
    if type(credits) is not int or not 0 <= credits <= 10:
        raise ValueError("Unverified linked account credit balance")
    try:
        normalized = str(uuid.UUID(account_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Linked canonical UUID required") from None
    if normalized != account_id:
        raise ValueError("Noncanonical linked account")
    return VerifiedWebIdentity("telegram", actor.subject, account_id)


def canonical_staging_account(actor):
    """Accept only authenticated provider-neutral account actors from staging.

    This validates shape; the caller MUST also verify the corresponding
    signed browser session and, for Telegram, the linked DB mapping.
    """
    if not isinstance(actor, VerifiedWebIdentity) or actor.account_id is None:
        raise ValueError("Verified canonical account required")
    try:
        account_id = str(uuid.UUID(actor.account_id))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Invalid canonical account") from None
    if account_id != actor.account_id:
        raise ValueError("Noncanonical account")
    if actor.provider == "google":
        if actor.subject != account_id:
            raise ValueError("Google actor mismatch")
    elif actor.provider == "telegram":
        if (not isinstance(actor.subject, str) or not actor.subject.isascii()
                or not actor.subject.isdecimal()
                or actor.subject.startswith("0")
                or not 0 < int(actor.subject) <= 9223372036854775807):
            raise ValueError("Telegram actor mismatch")
    else:
        raise ValueError("Unsupported provider")
    return account_id

def may_link_accounts(google_actor, telegram_actor, *, both_sessions_verified=False):
    """A linking request may START only after BOTH independently verified proofs.

    No linking is performed here, and this NEVER changes credits, payments,
    or legacy Telegram identities.
    """
    return (both_sessions_verified is True
            and isinstance(google_actor, VerifiedWebIdentity)
            and isinstance(telegram_actor, VerifiedWebIdentity)
            and google_actor.provider == "google"
            and google_actor.account_id == google_actor.subject
            and telegram_actor.provider == "telegram"
            and telegram_actor.account_id is None)
