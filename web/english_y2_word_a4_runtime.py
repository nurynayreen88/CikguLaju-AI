"""Word-only five-Lesson Year 2 English A4 compactor.

No database writes, changes to user credits or Telegram delivery callbacks.
Reuses the already deployed text-preserving Year 6 Word A4 compactor, but only
for explicitly verified overflow lessons 2,3,12,13,14 of English Year 2.
"""
import re
from web.english_y6_word_a4_runtime import compact_word_file

OVERFLOW_LESSONS = frozenset((2, 3, 12, 13, 14))


def _target(state):
    if not isinstance(state, dict):
        return False
    if str(state.get("task") or "").strip().casefold() != "rph":
        return False
    subject = re.sub(r"[^a-z]", "", str(state.get("subject") or "").casefold())
    if subject not in ("english", "bahasainggeris", "bi"):
        return False
    year = str(state.get("year") or state.get("year_label") or "").strip().casefold()
    if year not in ("2", "tahun 2", "year 2", "primary year 2", "y2", "tahun 2 (sk)"):
        return False
    raw = state.get("lesson_no")
    if raw is None or raw == "":
        raw = state.get("textbook_lesson_no")
    if raw is None or raw == "":
        raw = state.get("lesson")
    if type(raw) is int:
        lesson = raw
    elif isinstance(raw, str) and raw.strip().isascii() and raw.strip().isdecimal():
        lesson = int(raw.strip())
    else:
        return False
    return lesson in OVERFLOW_LESSONS


def install(runtime):
    """Wrap Word export at the final output layer, fail-closed for all other RPH."""
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y2_WORD_A4_ACTIVE", False):
        return True
    previous = getattr(runtime, "create_word_file", None)
    if not callable(previous):
        return False

    def year2_word(state, *args, **kwargs):
        path = previous(state, *args, **kwargs)
        if _target(state):
            # The helper saves to a temporary file and atomically replaces the
            # original only on success; failed compaction leaves original intact.
            compact_word_file(path)
        return path

    runtime.create_word_file = year2_word
    runtime.CIKGULAJU_ENGLISH_Y2_WORD_A4_ACTIVE = True
    return True
