"""Source-linked reflection for RBT and Sejarah draft RPH, without changing source rows."""
import re


def source_reflection(state, criterion, original):
    manual = state.get("rph_teacher_reflection")
    if isinstance(manual, str) and manual.strip():
        return manual
    if str(state.get("rph_reflection_mode") or "").casefold() == "manual":
        return ""
    if original and not re.search(r"murid mencapai (?:objektif|kriteria kejayaan)", original, re.I):
        return original
    # Remove only the teacher's assessment instruction, not the pupils' target.
    evidence = re.split(r";\s*guru menilai\b", criterion.strip(), maxsplit=1, flags=re.I)[0].rstrip(". ")
    if not evidence:
        return original
    return "____ / ____ mencapai sasaran: " + evidence + ". Baki dibimbing."
