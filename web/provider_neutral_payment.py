"""Provider-neutral payment identity and plan validation helpers.

Pure checks only. Existing Telegram payment approval routes are untouched.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import uuid


@dataclass(frozen=True)
class PaymentActor:
    account_id: str
    provider: str


def verified_payment_actor(account_id, provider):
    """Only canonical UUID accounts can enter the new Web payment queue."""
    try:
        canonical = str(uuid.UUID(str(account_id)))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Verified Web account required") from None
    if canonical != account_id or provider not in ("google", "telegram"):
        raise ValueError("Verified Web account required")
    return PaymentActor(canonical, provider)


def validate_payment_plan(plan_code, approved_catalog):
    """Never trust an amount, duration or access grant sent by the browser."""
    if not isinstance(plan_code, str) or not isinstance(approved_catalog, dict):
        raise ValueError("Approved plan catalog required")
    entry = approved_catalog.get(plan_code)
    if not isinstance(entry, dict) or entry.get("enabled") is not True:
        raise ValueError("Plan unavailable")
    amount = entry.get("amount_sen")
    if type(amount) is not int or not 1 <= amount <= 10000000:
        raise ValueError("Invalid approved price")
    if plan_code not in ("rakan_pembangun", "monthly", "annual"):
        raise ValueError("Unsupported plan")
    return plan_code, amount


def can_resubmit_payment(current_status):
    """Reject/reupload uses a NEW payment request; never mutate old receipts."""
    return current_status in (None, "rejected")


def payment_review_action(action, *, admin_verified):
    if admin_verified is not True or action not in ("approve", "reject"):
        raise PermissionError("Admin verification required")
    return action
