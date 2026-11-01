"""Read-only dropdown options for Web V1 staging."""
from web_v1_verified_topics import SUBJECTS
from web_v1_verified_pdp import VerifiedPdpCatalog


def subject_options(year):
    if type(year) is not int or year not in range(1, 7):
        raise ValueError('invalid year')
    return [{'value': code, 'label': label} for code, label in SUBJECTS.items()]


def unit_options(database_path, year, subject_code):
    records = VerifiedPdpCatalog(database_path).list_pdp(year=year, subject_code=subject_code)
    names = dict.fromkeys((r.get('unit_title') or '').strip() for r in records)
    return [{'value': name, 'label': name} for name in names if name]


def pdp_options(database_path, year, subject_code, unit_title):
    if not isinstance(unit_title, str) or not unit_title.strip():
        raise ValueError('invalid unit')
    records = VerifiedPdpCatalog(database_path).list_pdp(year=year, subject_code=subject_code)
    available_units = {(r.get('unit_title') or '').strip() for r in records}
    if unit_title.strip() not in available_units:
        return []
    return [{'value': str(r['id']), 'label': 'PdP ' + str(r['pdp_no']) + ' — ' + str(r.get('subtopic') or r.get('topic') or ''), 'standalone_rph_verified': False} for r in records if (r.get('unit_title') or '').strip() == unit_title]
