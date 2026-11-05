"""Risk assessment for browser retries and credit accounting.

This module deliberately does not implement a memory-only deduplication cache.
Such a cache would fail across Gunicorn workers, process restarts, and Render
instances. Use a durable, user-bound request ledger before public activation.
"""

RETRY_SAFETY_REQUIREMENTS = (
    "Browser supplies a per-click idempotency key, bound to authenticated user.",
    "Server stores key, lesson, format, approval version and immutable result in durable storage.",
    "A second request with the same key and payload replays the same result without another debit.",
    "Same key with a different payload is rejected.",
    "Concurrent workers must atomically claim one request; only the winner renders and debits.",
    "A pending or unknown RPC result must be reconciled against the shared ledger before retry.",
    "An interrupted HTTP transfer requires a replayable document or an auditable refund.",
    "Do not use in-process locks, global dicts or session cookies as the sole ledger.",
)


def public_download_ready(*, durable_idempotency, delivery_replay,
                          production_layout_parity, approval_verified,
                          trial_policy_verified):
    """Explicit release gate; never infer safety from green unit tests."""
    flags = (durable_idempotency, delivery_replay, production_layout_parity,
             approval_verified, trial_policy_verified)
    if any(type(flag) is not bool for flag in flags):
        raise ValueError("Release checks must be explicit booleans")
    return all(flags)
