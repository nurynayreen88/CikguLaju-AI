"""Source-linked reflection for RBT/Sejarah draft native row adapters.

Only replace the known generic source template. Keep manual teacher text
and leave outcomes unfilled. Source learning targets are not rewritten.
"""
import re

def source_reflection(state, original, criterion):
    manual = str(state.get("rph_teacher_reflection") or "").strip()
    if manual:
        return manual
    if str(state.get("rph_reflection_mode") or "").casefold() == "manual":
        return original
    if not re.search(r"murid mencapai objektif[.;]", original, re.I):
        return original
    evidence = " ".join(criterion.split()).split("; guru menilai", 1)[0].rstrip(".; ")
    evidence = re.sub(r"^Murid (?:dapat )?", "", evidence, flags=re.I)
    if not evidence:
        return original
    return "____ / ____ murid mencapai sasaran: " + evidence + ". Baki dibimbing semula."
