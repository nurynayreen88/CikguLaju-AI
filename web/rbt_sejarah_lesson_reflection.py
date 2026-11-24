"""Source-specific draft reflection for the RBT and Sejarah native bridges.

No pupil attainment is assumed; explicit manual input is authoritative.
Keep draft academic status and source text untouched.
"""
import re

def lesson_reflection(state, criterion, objective, original):
    manual = str(state.get("rph_teacher_reflection") or "").strip()
    if manual:
        return manual
    if str(state.get("rph_reflection_mode") or "").casefold() == "manual":
        return original
    if not re.search(r"murid mencapai (?:objektif|kriteria kejayaan)", original or "", re.I):
        return original
    candidates = [criterion] + (objective if isinstance(objective,list) else [objective])
    for raw in candidates:
        if not isinstance(raw,str):
            continue
        evidence = " ".join(raw.split()).rstrip(".")
        if not evidence or re.search(r"seperti dalam objektif|mengikut objektif|mengikut SP|fokus pembelajaran", evidence, re.I):
            continue
        # Keep entire source sentences, never cut learning requirements.
        if len(evidence) <= 155:
            return "____ / ____ murid mencapai sasaran: " + evidence + ". Baki dibimbing."
    return original
