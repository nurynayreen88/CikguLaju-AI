"""Opt-in runtime bridge: use existing Year 4 standalone RPH for selected Lesson.

Does not alter database, source lesson files, or other subjects/years.
"""
import re
from english_standalone_adapter import get_english_rph


def install(runtime):
    original = getattr(runtime, "_local_rph_text", None)
    year_number = getattr(runtime, "_english_primary_year_number_v2517", None)
    if not callable(original) or not callable(year_number):
        return False

    def specific_rph(state):
        if not isinstance(state, dict):
            return original(state)
        subject = re.sub(r"[^a-z]", "", str(state.get("subject") or "").casefold())
        if subject not in ("english", "bahasainggeris", "bi"):
            return original(state)
        if year_number(state.get("year")) != 4:
            return original(state)
        lesson = state.get("lesson_no") or state.get("textbook_lesson_no") or state.get("lesson")
        standalone = get_english_rph(4, "English", lesson)
        if standalone is None:
            return original(state)
        # Existing PDF/Word renderers expect plain text rather than raw Markdown.
        # Preserve full instructional content and all verified page/track references.
        standalone = re.sub(r"(?m)^#{1,3}\s+", "", standalone)
        standalone = re.sub(r"\*\*(.*?)\*\*", r"\1", standalone)
        return standalone

    runtime._local_rph_text = specific_rph
    return True
