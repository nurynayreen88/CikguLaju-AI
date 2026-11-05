"""Source-consistency policy for Telegram/Web.

Shared SQLite provenance is necessary for the current read-only catalog, but
not sufficient to establish parity of RPH, attachments, approvals or quota.
This is an explicit audit contract, not an assertion that live sync exists.
"""

SHARED_DOMAINS = (
    "lesson_catalog",
    "rpt_sequence",
    "rph_approved_content",
    "textbooks_and_workbooks",
    "audio_tracks",
    "material_approvals",
    "user_entitlements",
    "trial_ledger",
)


def parity_report(verified_domains):
    """Return a conservative report for independently verified domains.

    Unknown domains are rejected to avoid silently claiming coverage.
    """
    if not isinstance(verified_domains, dict):
        raise ValueError("Verification mapping required")
    unknown = set(verified_domains) - set(SHARED_DOMAINS)
    if unknown:
        raise ValueError("Unknown parity domain")
    if any(type(value) is not bool for value in verified_domains.values()):
        raise ValueError("Parity flags must be booleans")
    domains = {domain: verified_domains.get(domain, False) for domain in SHARED_DOMAINS}
    return {"fully_shared": all(domains.values()), "domains": domains,
            "unverified": [key for key, ok in domains.items() if not ok]}
