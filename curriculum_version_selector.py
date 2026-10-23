"""Non-destructive curriculum-version selection policy for CikguLaju.

KP2027 is opt-in and fail-closed until exact scope and source mapping are approved.
This module does not change the existing default flow or database.
"""
LEGACY = "existing"
KP2027 = "kp2027"
OPTIONS = (
    {"id": LEGACY, "label": "KSSR/KSSM Sedia Ada", "default": True},
    {"id": KP2027, "label": "Kurikulum Persekolahan 2027 (KP2027)", "default": False},
)

def curriculum_options():
    return [dict(option) for option in OPTIONS]

def resolve_curriculum(version=None, year_label=None, subject=None, verified_scopes=()):
    version = version or LEGACY
    if version == LEGACY:
        return {"version": LEGACY, "enabled": True, "reason": None}
    if version != KP2027:
        raise ValueError("Unknown curriculum version")
    if year_label not in {"Tahun 1", "Tingkatan 1"}:
        return {"version": KP2027, "enabled": False, "reason": "NOT_IN_2027_ROLLOUT"}
    if not subject or (year_label, subject) not in verified_scopes:
        return {"version": KP2027, "enabled": False, "reason": "SOURCE_MAPPING_NOT_VERIFIED"}
    return {"version": KP2027, "enabled": True, "reason": None}
