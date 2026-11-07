"""Build Supabase REST/Storage service headers for *staging backend only*.

Supabase's new sb_secret_ keys are API keys, not JWTs. Sending one as
Authorization: Bearer causes Invalid JWT; legacy service_role keys are JWTs.
Keep the privileged key out of every browser response and client-side file.
"""


def staging_service_headers(key, *, accept="application/json"):
    if not isinstance(key, str) or len(key) < 24:
        raise ValueError("Missing staging backend secret")
    if key.startswith("sb_publishable_"):
        raise ValueError("Publishable key cannot authorize backend operations")
    headers = {"apikey": key, "Accept": accept}
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    return headers
