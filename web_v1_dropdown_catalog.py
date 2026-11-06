"""Read-only dropdown options for Web V1 staging."""
import re
from web_v1_verified_topics import SUBJECTS
from web_v1_verified_pdp import VerifiedPdpCatalog, list_explicit_pjpk_entries


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

def _navigation_records(database_path, year, subject_code, component=None):
    if subject_code == 'PJPK':
        if component not in ('PJ', 'PK'):
            raise ValueError('PJPK requires verified PJ or PK component')
        return list_explicit_pjpk_entries(database_path, year, component)
    if component not in (None, ''):
        raise ValueError('component only applies to PJPK')
    return VerifiedPdpCatalog(database_path).list_pdp(year=year, subject_code=subject_code)


def unit_options(database_path, year, subject_code, component=None):
    records = _navigation_records(database_path, year, subject_code, component)
    names = dict.fromkeys((r.get('unit_title') or '').strip() for r in records)
    return [{'value': name, 'label': name} for name in names if name]


def _pi_verified_page_refs(database_path, year):
    """Only expose source pages from the verified PI PdP details table."""
    import sqlite3
    from pathlib import Path
    path = Path(database_path)
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as con:
        con.execute("PRAGMA query_only=ON")
        if not con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='pi_pdp_details_v2591'"
        ).fetchone():
            return {}
        rows = con.execute(
            """SELECT pdp_no,textbook_pages
               FROM pi_pdp_details_v2591
               WHERE year_label=? AND verified=1
               ORDER BY pdp_no LIMIT 1001""",
            (f"Tahun {year}",)
        ).fetchall()
    if len(rows) > 1000:
        raise ValueError("PI source too large")
    pages = {}
    for number, ref in rows:
        if type(number) is not int or not 0 < number <= 1000:
            continue
        value = str(ref or "").strip()
        if value and len(value) <= 120 and all(ord(c) >= 32 for c in value):
            pages.setdefault(number, set()).add(value)
    return {k: "Buku Teks m/s " + next(iter(v)) for k, v in pages.items()
            if len(v) == 1}


def pdp_options(database_path, year, subject_code, unit_title, component=None):
    if not isinstance(unit_title, str) or not unit_title.strip() or len(unit_title) > 300:
        raise ValueError('invalid unit')
    records = _navigation_records(database_path, year, subject_code, component)
    available_units = {(r.get('unit_title') or '').strip() for r in records}
    if unit_title.strip() not in available_units:
        return []
    pi_pages = (_pi_verified_page_refs(database_path, year)
                if subject_code == "PI" else {})
    result = []
    for r in records:
        if (r.get("unit_title") or "").strip() != unit_title:
            continue
        number = r.get("pdp_no")
        if type(number) is not int or not 0 < number < 10000:
            continue  # No invented PdP index.
        row = {'value': str(r['id']),
               'label': 'PdP ' + str(number) + ' — '
                        + str(r.get('subtopic') or r.get('topic') or ''),
               'pdp_no': number, 'standalone_rph_verified': False}
        if number in pi_pages:
            row['textbook_ref'] = pi_pages[number]
        result.append(row)
    return result


PJPK_COMPONENTS = (
    {"value": "PJ", "label": "Pendidikan Jasmani (PJ)"},
    {"value": "PK", "label": "Pendidikan Kesihatan (PK)"},
)


def component_options(subject_code):
    """PJPK alone has an extra choice; other subjects retain four steps."""
    return [dict(item) for item in PJPK_COMPONENTS] if subject_code == "PJPK" else []


def verified_component_records(records, subject_code, component=None):
    """Never infer PJ/PK from a title or include unclassified records."""
    if subject_code != "PJPK":
        if component not in (None, ""):
            raise ValueError("component is only valid for PJPK")
        return list(records)
    if component not in ("PJ", "PK"):
        raise ValueError("PJPK requires PJ or PK")
    return [record for record in records
            if record.get("component_verified") is True
            and record.get("component") == component]


_UNIT_TITLE_RE = re.compile(r"^(?:Unit|U)\s*0*([1-9]\d{0,2})\s*(?:[:：.\-–—]\s*)?(.+)$", re.I)
_UNIT_CODE_RE = re.compile(r"^(?:(?:Unit|U)\s*)?0*([1-9]\d{0,2})(?:\.0)?$", re.I)
_BM_SKILL_NAMES = frozenset({
    "kemahiran mendengar dan bertutur", "mendengar dan bertutur",
    "kemahiran membaca", "membaca", "kemahiran menulis", "menulis",
    "seni bahasa", "tatabahasa", "kemahiran seni bahasa",
    "kemahiran tatabahasa",
})


def display_unit_label(title, code=""):
    """Display an existing source unit number; never number inferred groups."""
    value = str(title or "").strip()
    if not value:
        return ""
    match = _UNIT_TITLE_RE.fullmatch(value)
    if match:
        return "Unit " + str(int(match.group(1))) + ": " + match.group(2).strip()
    code_match = _UNIT_CODE_RE.fullmatch(str(code or "").strip())
    if code_match:
        return "Unit " + str(int(code_match.group(1))) + ": " + value
    return value


def _bm_verified_structured_rows(database_path, year):
    """Read actual BM Tema/Unit/Tajuk from master RPT rows; refuse skill domains.

    Deliberately do not rewrite a synthetic 1.0–5.0 language-skill domain into
    a textbook unit. If the master DB does not contain a genuine hierarchy,
    return no invented alternatives.
    """
    import sqlite3
    from pathlib import Path
    if type(year) is not int or year not in range(1, 7):
        raise ValueError("Invalid BM school year")
    path = Path(database_path)
    if not path.is_file():
        raise FileNotFoundError("Master database unavailable")
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=ON")
        entries = [dict(row) for row in con.execute(
            """SELECT id,sequence_no,theme,unit_code,unit_title,topic,subtopic,skill_focus
               FROM rpt_entries WHERE year_label=? AND subject='Bahasa Melayu'
                 AND verified=1
                 AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'
               ORDER BY sequence_no,id LIMIT 1001""", (f"Tahun {year}",)
        )]
        if len(entries) > 1000:
            raise ValueError("Oversized BM source")
        # This map supplies pages only when the exact selected unit and PdP
        # lesson are independently verified; no page guess from a unit range.
        pages = {}
        table = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' "
            "AND name='textbook_page_lesson_map'"
        ).fetchone()
        if table:
            candidates = con.execute(
                """SELECT unit_title,lesson_no,content_topic,book_title,
                          page_start,page_end
                   FROM textbook_page_lesson_map
                   WHERE year_label=? AND subject='Bahasa Melayu'
                     AND verified=1 AND page_start IS NOT NULL
                     AND page_end IS NOT NULL
                   LIMIT 5001""", (f"Tahun {year}",)
            ).fetchall()
            if len(candidates) <= 5000:
                for candidate in candidates:
                    p = dict(candidate)
                    key = (str(p["unit_title"] or "").strip().casefold(),
                           str(p["lesson_no"] or "").strip())
                    pages.setdefault(key, []).append(p)
    result = []
    for row in entries:
        theme = str(row["theme"] or "").strip()
        unit = str(row["unit_title"] or "").strip()
        topic = str(row["topic"] or "").strip()
        code = str(row["unit_code"] or "").strip()
        if not theme or not unit or not topic:
            continue
        if (unit.casefold() in _BM_SKILL_NAMES
                or re.fullmatch(r"[1-5]\.0", code)
                or re.match(r"^kemahiran\b", unit, re.I)):
            continue
        row.update({"theme": theme, "unit_title": unit,
                    "topic": topic, "unit_code": code})
        key = (unit.casefold(), str(row["sequence_no"] or "").strip())
        candidates = [p for p in pages.get(key, []) if
                      not str(p["content_topic"] or "").strip()
                      or str(p["content_topic"]).strip().casefold() == topic.casefold()]
        distinct = {(p["book_title"], p["page_start"], p["page_end"]) for p in candidates}
        if len(distinct) == 1:
            book, first, last = next(iter(distinct))
            if (type(first) is int and type(last) is int
                    and 0 < first <= last <= 1000):
                row["textbook_ref"] = (
                    "Buku Teks m/s " + str(first)
                    + ("–" + str(last) if last != first else "")
                )
        result.append(row)
    return result


def bm_theme_options(database_path, year):
    rows = _bm_verified_structured_rows(database_path, year)
    return [{"value": title, "label": title}
            for title in dict.fromkeys(r["theme"] for r in rows)]


def bm_unit_options(database_path, year, theme):
    if not isinstance(theme, str) or not 0 < len(theme) <= 300:
        raise ValueError("Invalid BM theme")
    rows = [r for r in _bm_verified_structured_rows(database_path, year)
            if r["theme"] == theme]
    if not rows:
        return []
    result = []
    for title in dict.fromkeys(r["unit_title"] for r in rows):
        codes = {r["unit_code"] for r in rows if r["unit_title"] == title}
        code = next(iter(codes)) if len(codes) == 1 else ""
        result.append({"value": title, "label": display_unit_label(title, code)})
    return result


def bm_topic_options(database_path, year, theme, unit):
    if not isinstance(unit, str) or not 0 < len(unit) <= 300:
        raise ValueError("Invalid BM unit")
    rows = [r for r in _bm_verified_structured_rows(database_path, year)
            if r["theme"] == theme and r["unit_title"] == unit]
    return [{"value": title, "label": title}
            for title in dict.fromkeys(r["topic"] for r in rows)]


def bm_pdp_options(database_path, year, theme, unit, topic):
    if not isinstance(topic, str) or not 0 < len(topic) <= 300:
        raise ValueError("Invalid BM topic")
    rows = [r for r in _bm_verified_structured_rows(database_path, year)
            if r["theme"] == theme and r["unit_title"] == unit
            and r["topic"] == topic]
    result = []
    for r in rows:
        number = r["sequence_no"]
        if type(number) is not int or not 0 < number < 10000:
            continue
        title = str(r.get("subtopic") or topic).strip()
        entry = {"value": str(r["id"]), "label": f"PdP {number:03d} — {title}",
                 "pdp_no": number, "standalone_rph_verified": False}
        if r.get("textbook_ref"):
            entry["textbook_ref"] = r["textbook_ref"]
        result.append(entry)
    return result
