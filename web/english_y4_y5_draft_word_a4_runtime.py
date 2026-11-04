"""Scoped Word A4 compaction for remaining English Y4/Y5 draft previews.

The original source document remains intact if compaction fails. Year5's
nine teacher-choice proposals already use their own compact adapter and
are excluded. Native PDF, other years, DB, quotas, and callbacks unaffected.
"""
from web.english_y4_pending_draft_preview_runtime import (
    PENDING as Y4_PENDING, _selected_y4_lesson
)
from web.english_y5_standalone_runtime import (
    CHOICE_LESSONS as Y5_CHOICES, _target as _year5_lesson
)
from web.english_y6_word_a4_runtime import compact_word_file


def _target(state):
    if not isinstance(state, dict) or str(state.get("task") or "").strip().casefold() != "rph":
        return False
    n4 = _selected_y4_lesson(state)
    if n4 in Y4_PENDING:
        return True
    n5 = _year5_lesson(state)
    if n5 is not None and n5 not in Y5_CHOICES:
        return True
    return False


def install(runtime):
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y4_Y5_DRAFT_WORD_A4_ACTIVE", False):
        return True
    prior = getattr(runtime, "create_word_file", None)
    if not callable(prior):
        return False

    def targeted_english_word(state, *args, **kwargs):
        original_path = prior(state, *args, **kwargs)
        if _target(state):
            # Text-preserving and atomic. A failed adjustment never prevents
            # delivery of the original Word file.
            compact_word_file(original_path)
        return original_path

    runtime.create_word_file = targeted_english_word
    runtime.CIKGULAJU_ENGLISH_Y4_Y5_DRAFT_WORD_A4_ACTIVE = True
    return True
