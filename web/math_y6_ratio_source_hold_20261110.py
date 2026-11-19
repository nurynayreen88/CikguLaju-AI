"""Route audited legacy Year 6 Maths choices to verified 2027 units."""

# Each key is a verified identity in the legacy source. Values are 2027
# catalogue units. A reviewed unit is not a one-to-one Lesson replacement.
# See audits/matematik_y6_semak_menu_lama_20261119.md.
_REVIEWED_UNITS = {
    "MT6-PDP-004": "01",
    "MT6-PDP-006": "01",
    "MT6-PDP-022": "02",
    "MT6-PDP-025": "02",
    "MT6-PDP-027": "02",
    "MT6-PDP-030": "02",
    "MT6-PDP-031": "02",
    "MT6-PDP-032": "02",
    "MT6-PDP-034": "03",
    "MT6-PDP-037": "03",
    "MT6-PDP-038": "03",
    "MT6-PDP-046": "04",
    "MT6-PDP-047": "04",
    "MT6-PDP-067": "06",
    "MT6-PDP-068": "06",
    "MT6-PDP-076": "07",
    "MT6-PDP-078": "07",
    "MT6-PDP-079": "07",
    "MT6-PDP-080": "07",
    "MT6-PDP-081": "07",
    "MT6-PDP-082": "07",
    "MT6-PDP-083": "07",
    "MT6-PDP-084": "07",
}


def reviewed_math_y6_unit(year, subject, pdp_code):
    if type(year) is int and year == 6 and subject == "MATH" and isinstance(pdp_code, str):
        return _REVIEWED_UNITS.get(pdp_code)
    return None


def held_math_y6_legacy_source(year, subject, pdp_code, rows):
    """Keep the audited legacy identity held until its whole RPH is reviewed."""
    if not reviewed_math_y6_unit(year, subject, pdp_code) or not isinstance(rows, list) or not rows:
        return False
    return all(
        isinstance(row, dict)
        and str(row.get("pdp_sequence_code") or "").strip() == pdp_code
        for row in rows
    )
