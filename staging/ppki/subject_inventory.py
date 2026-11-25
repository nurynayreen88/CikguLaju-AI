"""PPKI subject inventory; distinct from the released lesson catalog.

Scope: KSSR Pendidikan Khas (Masalah Pembelajaran), Semakan 2017.
Asas 3M is a curriculum group, not a selectable subject.
Only existing Pengurusan Kehidupan has a connected catalog here.
Inventory entries must never imply downloadable materials.
"""
from staging.ppki.catalog import SUBJECT, YEARS

_COMMON = (
    ("BAHASA_INGGERIS_PPKI", "Bahasa Inggeris"),
    ("BAHASA_MELAYU_PPKI", "Bahasa Melayu"),
    ("MATEMATIK_PPKI", "Matematik"),
    ("PENDIDIKAN_ISLAM_PPKI", "Pendidikan Islam"),
    ("PENDIDIKAN_MORAL_PPKI", "Pendidikan Moral"),
    (SUBJECT, "Pengurusan Kehidupan"),
)
_LOWER = (
    ("PENDIDIKAN_JASMANI_PPKI", "Pendidikan Jasmani"),
    ("PENDIDIKAN_SENI_KREATIF_PPKI", "Pendidikan Seni Kreatif"),
)
_UPPER = (
    ("KEMAHIRAN_HIDUP_ASAS_PPKI", "Kemahiran Hidup Asas"),
    ("PENDIDIKAN_JASMANI_KESIHATAN_PPKI", "Pendidikan Jasmani dan Pendidikan Kesihatan"),
    ("PENDIDIKAN_MUZIK_PPKI", "Pendidikan Muzik"),
    ("PENDIDIKAN_SAINS_SOSIAL_ALAM_SEKITAR_PPKI", "Pendidikan Sains, Sosial dan Alam Sekitar"),
    ("PENDIDIKAN_SENI_VISUAL_PPKI", "Pendidikan Seni Visual"),
    ("PENDIDIKAN_TMK_PPKI", "Pendidikan Teknologi Maklumat dan Komunikasi"),
)
_ASAS_3M = frozenset(("BAHASA_INGGERIS_PPKI", "BAHASA_MELAYU_PPKI", "MATEMATIK_PPKI"))


def subject_inventory(year):
    """Return independently selectable subject identities and readiness metadata."""
    if type(year) is not int or year not in YEARS:
        raise ValueError("Unknown PPKI year")
    entries = sorted(_COMMON + (_LOWER if year <= 3 else _UPPER),
                     key=lambda entry: entry[1].casefold())
    return [
        {
            "value": key,
            "label": label,
            "curriculum_group": "Asas 3M" if year <= 3 and key in _ASAS_3M else label,
            "catalog_connected": key == SUBJECT,
            "status": "catalog_connected" if key == SUBJECT else "pending_source_audit",
        }
        for key, label in entries
    ]
