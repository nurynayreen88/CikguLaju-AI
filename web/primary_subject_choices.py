"""Primary subject variants shared by timetable and curriculum selectors."""
from functools import lru_cache

from primary_language_subjects import PRIMARY_LANGUAGE_SUBJECTS
from web.rpt_2027_all_http import DLP_SUBJECTS, PUBLISHED_YEARS, SJK_RPTS, document_path


@lru_cache(maxsize=1)
def subject_variants():
    """Keep timetable labels separate from the native SK generation codes."""
    rows = []
    for code, label in PRIMARY_LANGUAGE_SUBJECTS.items():
        rows.append({"code": code, "label": label, "curriculum": "kssr"})
    for definition in SJK_RPTS.values():
        rows.append({
            "code": definition.CODE, "label": definition.LABEL, "curriculum": "sjkc",
            "rpt_years": [year for year in definition.YEARS if definition.document_path(year)],
        })
    rows.append({"code": "matematik_sjkt", "label": "Matematik (SJKT)", "curriculum": "sjkt"})
    for code, label in DLP_SUBJECTS.items():
        rows.append({
            "code": code, "label": f"{label} (DLP)", "curriculum": "dlp",
            "rpt_years": [year for year in PUBLISHED_YEARS if document_path(code, year)],
            "rph_code": "SCIENCE_DLP" if code == "science_dlp" else "MATH_DLP",
        })
    return rows


@lru_cache(maxsize=1)
def variants_by_name():
    rows = {row["label"].casefold(): row for row in subject_variants()}
    for alias, label in (
        ("sains (dlp)", "science (dlp)"),
        ("matematik (dlp)", "mathematics (dlp)"),
        ("matematik sjkc", "matematik (sjkc)"),
        ("matematik sjkt", "matematik (sjkt)"),
        ("bahasa melayu (sjkc)", "bahasa melayu (sjk)"),
    ):
        rows[alias] = rows[label]
    return rows
