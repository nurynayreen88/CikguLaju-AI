"""Word A4 layout adjustment limited to nine Year 5 draft proposals.

Reuses the safe, text-preserving Year 6 Word compactor. No PDF/native
ReportLab, curriculum DB, user credits, or other years are changed.
"""
from web.english_y5_standalone_runtime import CHOICE_LESSONS, _target
from web.english_y6_word_a4_runtime import compact_word_file


def _is_choice_rph(state):
    return (isinstance(state, dict)
            and str(state.get("task") or "").strip().casefold() == "rph"
            and _target(state) in CHOICE_LESSONS)


def install(runtime):
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y5_CHOICE_A4_WORD_ACTIVE", False):
        return True
    prior = getattr(runtime, "create_word_file", None)
    if not callable(prior):
        return False

    def year5_choice_word(state, *args, **kwargs):
        path = prior(state, *args, **kwargs)
        if _is_choice_rph(state):
            # On failure the original DOCX stays intact and can still be sent.
            compact_word_file(path)
        return path

    runtime.create_word_file = year5_choice_word
    runtime.CIKGULAJU_ENGLISH_Y5_CHOICE_A4_WORD_ACTIVE = True
    return True
