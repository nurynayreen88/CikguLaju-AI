"""Read-only dropdown options for Web V1 staging."""
import re
from web.pi_navigation import PI_FIELD_ORDER
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
    if subject_code == "PI":
        names = dict.fromkeys([field for field in PI_FIELD_ORDER if field in names] + list(names))
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


def bm_sequence_token(year, theme, unit_code, unit_title, topic):
    """Opaque key for a real grouped BM PdP, not a guessed RPT row ID."""
    import hashlib
    if type(year) is not int or year not in range(1, 7):
        raise ValueError("Invalid BM year")
    parts = [str(x or "").strip() for x in (theme, unit_code, unit_title, topic)]
    if not all(parts[i] for i in (0, 2, 3)):
        raise ValueError("Incomplete native BM lesson identity")
    return "b" + hashlib.sha256(
        (str(year) + "\x00" + "\x00".join(parts)).encode("utf-8")
    ).hexdigest()[:24]


def _bm_verified_structured_rows(database_path, year):
    """The exact BM source used by Telegram _bm96_rows, read-only.

    Telegram's BM Tema → Unit → Tajuk PdP menu reads verified_pdp_sequence.
    rpt_entries contains broad skill domains and MUST NOT supply BM menus.
    No migrations, schema changes, RPT fallbacks, or guessed lesson IDs.
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
        rows = [dict(row) for row in con.execute(
            """SELECT * FROM verified_pdp_sequence
               WHERE year_label=? AND subject='Bahasa Melayu'
                 AND COALESCE(verification_status,'')
                   NOT IN ('REJECT_NON_SK','SOURCE_NONCORE','REJECTED')
               ORDER BY CASE WHEN week_no IS NULL THEN 999 ELSE week_no END,id
               LIMIT 5001""", (f"Tahun {year}",)
        )]
        if len(rows) > 5000:
            raise ValueError("Oversized verified BM sequence")
    result = []
    for r in rows:
        theme = str(r.get("theme") or "").strip()
        unit = str(r.get("unit_title") or "").strip()
        topic = str(r.get("pdp_title") or "").strip()
        code = str(r.get("unit_code") or "").strip()
        if not theme or not unit or not topic:
            continue
        if (unit.casefold() in _BM_SKILL_NAMES or
                re.match(r"^kemahiran\b", unit, re.I)):
            continue
        r.update({"theme": theme, "unit_code": code,
                  "unit_title": unit, "topic": topic})
        result.append(r)
    # Hide incomplete PdP groups before exposing their Tema or Unit. Telegram
    # itself refuses to commit such a group until SK/SP is present.
    valid = {
        (r["theme"], r["unit_code"], r["unit_title"], r["topic"])
        for r in result
        if str(r.get("sk_code") or "").strip()
        and str(r.get("sp_code") or "").strip()
    }
    for r in result:
        r["navigation_theme"] = r["theme"]
        if (year == 5 and
                (bm_theme_identity(r["theme"]), r["unit_code"], r["unit_title"], r["topic"])
                == (bm_theme_identity("Tema 1: Keluarga Berwawasan"),
                    "1", "Masyarakat Penyayang", "Bank Rezeki Bergerak")):
            r["navigation_theme"] = "Tema 1: Kemasyarakatan"
    return [
        r for r in result
        if (r["theme"], r["unit_code"], r["unit_title"], r["topic"]) in valid
    ]


_BM_NUMBERED_THEME_RE = re.compile(
    r"^(?:TEMA\s*)?([1-9]\d?)\s*[.:\-–—)]\s*(\S.*)$", re.I,
)


def bm_theme_identity(raw):
    """Semantic identity ONLY when both official theme number and title match.

    Source rows are never modified. Different titles under the same theme
    number (which exist in Year 5 master data) deliberately remain distinct.
    """
    title = re.sub(r"\s+", " ", str(raw or "")).strip()
    match = _BM_NUMBERED_THEME_RE.fullmatch(title)
    if match:
        return ("numbered", int(match[1]), match[2].casefold())
    return ("verbatim", title.casefold())


def bm_theme_display(raw):
    title = re.sub(r"\s+", " ", str(raw or "")).strip()
    match = _BM_NUMBERED_THEME_RE.fullmatch(title)
    if not match:
        return title
    name = match[2].strip()
    # Keep source spelling for mixed-case titles and existing acronyms.
    if name.isupper():
        name = name.title()
    return f"Tema {int(match[1])}: {name}"


def bm_theme_options(database_path, year):
    rows = _bm_verified_structured_rows(database_path, year)
    found = {}
    for r in rows:
        raw = r["navigation_theme"]
        found.setdefault(bm_theme_identity(raw), bm_theme_display(raw))
    return [{"value": title, "label": title} for title in found.values()]


def _bm_unit_key(title):
    return " ".join(title.split()).casefold()


def bm_unit_options(database_path, year, theme):
    if not isinstance(theme, str) or not 0 < len(theme) <= 300:
        raise ValueError("Invalid BM theme")
    identity = bm_theme_identity(theme)
    groups = {}
    for row in _bm_verified_structured_rows(database_path, year):
        if bm_theme_identity(row["navigation_theme"]) == identity:
            groups.setdefault(_bm_unit_key(row["unit_title"]), []).append(row)
    result = []
    for rows in groups.values():
        title = rows[0]["unit_title"]
        codes = {row["unit_code"] for row in rows}
        code = next(iter(codes)) if len(codes) == 1 else ""
        result.append({"value": title, "label": display_unit_label(title, code)})
    return result


def bm_topic_options(database_path, year, theme, unit):
    if not isinstance(unit, str) or not 0 < len(unit) <= 300:
        raise ValueError("Invalid BM unit")
    identity = bm_theme_identity(theme)
    selected_unit = _bm_unit_key(unit)
    rows = [r for r in _bm_verified_structured_rows(database_path, year)
            if bm_theme_identity(r["navigation_theme"]) == identity
            and _bm_unit_key(r["unit_title"]) == selected_unit]
    return [{"value": title, "label": title}
            for title in dict.fromkeys(r["topic"] for r in rows)]


def bm_pdp_options(database_path, year, theme, unit, topic):
    if not all(isinstance(v, str) and 0 < len(v.strip()) <= 300
               for v in (theme, unit, topic)):
        raise ValueError("Invalid BM lesson selection")
    all_rows = _bm_verified_structured_rows(database_path, year)
    groups = {}
    for r in all_rows:
        key = (r["theme"], r["unit_code"], r["unit_title"], r["topic"])
        groups.setdefault(key, []).append(r)
    # The ordinal is ONLY a navigation number, determined by real Telegram
    # PdP group order. It does not claim to be an official SOW lesson number.
    choices = []
    for idx, (key, members) in enumerate(groups.items(), 1):
        _, _, title, name = key
        row_theme = bm_theme_identity(members[0]["navigation_theme"])
        if (row_theme, _bm_unit_key(title), name) != (bm_theme_identity(theme), _bm_unit_key(unit), topic):
            continue
        if not any(str(r.get("sk_code") or "").strip()
                   and str(r.get("sp_code") or "").strip() for r in members):
            continue
        token = bm_sequence_token(year, *key)
        seqs = {int(r["source_sequence_no"]) for r in members
                if str(r.get("source_sequence_no") or "").isdigit()
                and 0 < int(r["source_sequence_no"]) < 10000}
        number = next(iter(seqs)) if len(seqs) == 1 else idx
        item = {"value": token, "label": f"PdP {number:03d} — {name}",
                "pdp_no": number, "standalone_rph_verified": False}
        if title != unit:
            item["origin_unit"] = title
        refs = {str(r.get("textbook_ref") or "").strip() for r in members
                if str(r.get("textbook_ref") or "").strip()}
        if len(refs) == 1:
            item["textbook_ref"] = next(iter(refs))
        choices.append(item)
    return choices

