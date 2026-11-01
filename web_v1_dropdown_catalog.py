"""Read-only dropdown options for Web V1 staging."""
from web_v1_verified_topics import SUBJECTS
from web_v1_verified_pdp import VerifiedPdpCatalog


def subject_options(year):
    if type(year) is not int or year not in range(1, 7):
        raise ValueError('invalid year')
    return [{'value': code, 'label': label} for code, label in SUBJECTS.items()]



def available_subject_options(database_path, year):
    """Show only subjects with verified RPT entries in the selected year."""
    import sqlite3
    from pathlib import Path
    subject_options(year)
    path = Path(database_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=2) as conn:
        conn.execute("PRAGMA query_only=ON")
        rows = conn.execute(
            "SELECT DISTINCT subject FROM rpt_entries WHERE year_label=? AND verified=1 "
            "AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'",
            (f"Tahun {year}",),
        ).fetchall()
    available = {row[0] for row in rows}
    return [{'value': code, 'label': label} for code, label in SUBJECTS.items() if label in available]

def unit_options(database_path, year, subject_code):
    records = VerifiedPdpCatalog(database_path).list_pdp(year=year, subject_code=subject_code)
    names = dict.fromkeys((r.get('unit_title') or '').strip() for r in records)
    return [{'value': name, 'label': name} for name in names if name]


def pdp_options(database_path, year, subject_code, unit_title):
    if not isinstance(unit_title, str) or not unit_title.strip() or len(unit_title) > 300:
        raise ValueError('invalid unit')
    records = VerifiedPdpCatalog(database_path).list_pdp(year=year, subject_code=subject_code)
    available_units = {(r.get('unit_title') or '').strip() for r in records}
    if unit_title.strip() not in available_units:
        return []
    return [{'value': str(r['id']), 'label': 'PdP ' + str(r['pdp_no']) + ' — ' + str(r.get('subtopic') or r.get('topic') or ''), 'standalone_rph_verified': False} for r in records if (r.get('unit_title') or '').strip() == unit_title]
