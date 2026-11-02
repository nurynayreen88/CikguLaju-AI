"""Pure validation helpers for independently verified TNG references.

Staging only: does not approve payments or connect to Supabase.
"""
import re

def normalize_transaction_reference(value):
    """Trim surrounding whitespace, uppercase ASCII reference, reject ambiguity."""
    if not isinstance(value, str):
        raise ValueError("Transaction reference must be text")
    ref = value.strip().upper()
    if not 6 <= len(ref) <= 100:
        raise ValueError("Transaction reference length invalid")
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9/_-]*", ref):
        raise ValueError("Transaction reference contains unsupported characters")
    if ref.startswith(("PIONEER-PAYMENT:", "PAYMENT-REQUEST:", "ADMIN:")):
        raise ValueError("Internal grant IDs are not bank references")
    return ref

def transaction_key(provider, merchant_account_key, bank_reference):
    if not provider or not merchant_account_key:
        raise ValueError("Provider and merchant account required")
    return (provider.strip().upper(), merchant_account_key.strip(),
            normalize_transaction_reference(bank_reference))
