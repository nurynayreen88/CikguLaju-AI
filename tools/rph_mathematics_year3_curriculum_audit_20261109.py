"""Read-only quality audit for Mathematics Year 3 'Wang', not a release flag.

KSSR Semakan 2017 original and optional KSSR Edisi 3 have different SK/SP.
This module never changes RPH files, source databases or user accounts.
"""
import re

CURRICULA = {
    "DSKP2017": {"sk": "4.4", "sp": "4.4.1", "scope": ("darab",)},
    "EDISI3": {"sk": "4.2", "sp": "4.2.1", "scope": ("darab", "bahagi")},
}
SK = re.compile(r"(?<![\d.])\d+\.\d+(?![\d.])")
SP = re.compile(r"(?<![\d.])\d+\.\d+\.\d+(?![\d.])")
GENERIC = re.compile(
    r"menunjukkan\s+pengetahuan\s+atau\s+kemahiran\s+berdasarkan|"
    r"mencapai\s+(?:kemahiran|objektif)\s+berdasarkan\s+standard",
    re.IGNORECASE,
)
TARGET = re.compile(r"\b(\d+)\s*(?:daripada|/)\s*(\d+)\b", re.IGNORECASE)


def audit_math_year3_wang(record: dict) -> dict:
    """Return HOLD or EDITORIAL_REVIEW_REQUIRED, never automatic FINAL READY.

    phases = [{title: str, minutes: int, teacher: str, pupils: str}, ...].
    Source pages must have explicitly verified textbook-page evidence.
    """
    if not isinstance(record, dict):
        raise TypeError("Expected a structured RPH dictionary")
    if record.get("subject") != "MATEMATIK" or record.get("year") != 3:
        raise ValueError("This SK/SP audit applies only to Matematik Tahun 3")
    ref = CURRICULA.get(record.get("edition"))
    problems = []
    sk_codes = SK.findall(str(record.get("sk") or ""))
    sp_codes = SP.findall(str(record.get("sp") or ""))
    if len(sk_codes) != len(set(sk_codes)):
        problems.append("DUPLICATE_SK")
    if ref is None:
        problems.append("CURRICULUM_EDITION_UNKNOWN")
    else:
        if sk_codes != [ref["sk"]]:
            problems.append("SK_EDITION_MISMATCH")
        if sp_codes != [ref["sp"]]:
            problems.append("SP_EDITION_MISMATCH")

    objective = str(record.get("objective") or "")
    criteria = str(record.get("criteria") or "")
    if GENERIC.search(objective):
        problems.append("GENERIC_OBJECTIVE")
    if not objective.strip() or not criteria.strip():
        problems.append("MISSING_OBJECTIVE_OR_CRITERIA")
    ratios = TARGET.findall(objective + " " + criteria)
    if not ratios or any(
        not 0 < int(numerator) <= int(denominator) <= 20
        for numerator, denominator in ratios
    ):
        problems.append("NO_MEASURABLE_CRITERION")

    phases = record.get("phases")
    if not isinstance(phases, list) or not phases:
        problems.append("MISSING_PHASES")
        phases = []
    total = 0
    for p in phases:
        if not isinstance(p, dict) or type(p.get("minutes")) is not int:
            problems.append("INVALID_PHASE")
            continue
        if p["minutes"] <= 0:
            problems.append("INVALID_PHASE")
        total += p["minutes"]
        if not str(p.get("teacher") or "").strip() or not str(p.get("pupils") or "").strip():
            problems.append("TEACHER_PUPIL_ACTIONS_MISSING")
    duration = record.get("duration_minutes")
    if type(duration) is not int or duration <= 0:
        problems.append("INVALID_SLOT_TIME")
    elif total != duration:
        problems.append("ACTIVITIES_EXCEED_OR_UNDERFILL_SLOT")

    activity = " ".join(
        str(p.get("teacher") or "") + " " + str(p.get("pupils") or "")
        for p in phases if isinstance(p, dict)
    ).casefold()
    if ref is not None:
        if any(word not in activity for word in ref["scope"]):
            problems.append("SP_OPERATION_COVERAGE_MISSING")
        if not all(re.search(r"\b" + factor + r"\b", activity)
                   for factor in ("10", "100", "1000")):
            problems.append("FACTOR_COVERAGE_NOT_EVIDENCED")
    if record.get("textbook_page") and not record.get("textbook_page_proof"):
        problems.append("UNVERIFIED_TEXTBOOK_PAGE")

    problems = sorted(set(problems))
    return {
        "year": 3, "subject": "MATEMATIK",
        "edition": record.get("edition"),
        "sk_expected": ref["sk"] if ref else None,
        "sp_expected": ref["sp"] if ref else None,
        "minutes": total,
        "issues": problems,
        "status": "HOLD" if problems else "EDITORIAL_REVIEW_REQUIRED",
        "publication_ready": False,
    }
