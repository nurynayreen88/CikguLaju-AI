"""Manual-review gate for historical CikguLaju worksheet blueprint records.

Purposefully impossible to return READY: a legacy 'verified_alignment=1'
means curriculum indexing, not print-ready or pedagogically reviewed work.
This module never reads databases or changes user-facing content itself.
"""
import re

PRIMARY_YEARS = frozenset("Tahun " + str(n) for n in range(1, 7))
PRIMARY_SUBJECTS = frozenset((
    "Bahasa Melayu", "Bahasa Inggeris", "Matematik", "Sains"
))
REQUIRED_FIELDS = ("year_label", "subject", "sk_code", "sp_code", "title",
                   "instructions", "question_pattern", "answer_space")
META_PATTERNS = (
    ("INSTRUCTION_TO_GENERATOR", re.compile(
        r"\b(?:sertakan semua|sediakan (?:gambar|ayat|perkataan|soalan|item)|"
        r"include all words|include all|provide (?:all|the)|"
        r"lengkapkan (?:latihan|item) (?:asas|berpandu) berkaitan|"
        r"complete a short supported task related to|"
        r"kenal pasti atau padankan maklumat asas berkaitan)\b", re.I)),
    ("RENDER_PLACEHOLDER", re.compile(
        r"\[(?:ANSWERSPACE|IMAGE|PICTURE|QUESTION|PROMPT|VISUAL)\s*:", re.I)),
    ("GENERIC_LEVEL_TITLE", re.compile(
        r"^(?:Aras|Level)\s*[1-9]\d*$", re.I)),
)
NUMBERED_QUESTION = re.compile(r"(?:^|\n)\s*(?:[1-9]\d?[.)]|\([1-9]\d?\))\s+")
MAX_LENGTH = 50000


def assess_legacy_blueprint(record):
    """Classify candidate for repair vs human review, never production READY.

    'REVIEW_REQUIRED' is an internal triage status only, never release permission.
    """
    if not isinstance(record, dict):
        return {"status": "REPAIR_REQUIRED", "reasons": ["INVALID_RECORD"],
                "public": False, "approved": False}
    reasons = []
    if record.get("year_label") not in PRIMARY_YEARS or record.get("subject") not in PRIMARY_SUBJECTS:
        reasons.append("OUTSIDE_PRIMARY_SCOPE")
    for key in REQUIRED_FIELDS:
        value = record.get(key)
        if not isinstance(value, (str, int, float)) or not str(value).strip():
            reasons.append("MISSING_" + key.upper())
        elif len(str(value)) > MAX_LENGTH:
            reasons.append("OVERSIZED_" + key.upper())
    title = str(record.get("title") or "")
    question = str(record.get("question_pattern") or "")
    instruction = str(record.get("instructions") or "")
    if META_PATTERNS[2][1].search(title):
        reasons.append("GENERIC_LEVEL_TITLE")
    combined = instruction + "\n" + question
    if META_PATTERNS[0][1].search(combined):
        reasons.append("INSTRUCTION_TO_GENERATOR")
    if META_PATTERNS[1][1].search(combined):
        reasons.append("RENDER_PLACEHOLDER")
    # A broad standard or activity topic does not establish actual pupil items.
    if len(question.strip()) < 55:
        reasons.append("INSUFFICIENT_PUPIL_CONTENT")
    if not NUMBERED_QUESTION.search(question):
        reasons.append("NO_EXPLICIT_ITEM_SEQUENCE")
    if str(record.get("verified_alignment")) not in ("1", "True"):
        reasons.append("CURRICULUM_ALIGNMENT_UNCONFIRMED")
    status = "REPAIR_REQUIRED" if reasons else "REVIEW_REQUIRED"
    return {"status": status, "reasons": sorted(set(reasons)),
            "public": False, "approved": False}
