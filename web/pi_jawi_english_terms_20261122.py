"""PI RPH: narrowly translate English teaching-method labels into Jawi.

This is a read-time display adapter for the original verified Telegram RPH.
It DOES NOT edit the source database, SK/SP, objectives, activity sequence,
teacher fields, other subjects, or Word/PDF presentation.
"""
from __future__ import annotations

import re
from functools import wraps

# Exact method labels only. Order matters: combined bilingual labels first.
# Jawi counterparts convey the same classroom method, not rewritten activities.
_REPLACEMENTS = (
    (r"role\s*[-–—]\s*play\s*\(\s*main\s+peranan\s*\)",
     "لاكونن ڤرانن"),
    (r"personal\s+learning\s+experiences\s*\(\s*pengalaman\s+peribadi\s*\)",
     "ڤڠالمن ڤريبادي"),
    (r"puzzle\s+it\s+out\s*[-–—]\s*selesaikan",
     "سلسايکن تيکاته-تيکي"),
    (r"spin\s*[-–—]?\s*n\s*[-–—]\s*think",
     "ڤوتر دان فيکير"),
    (r"stay\s*(?:&|and)\s*stray",
     "ککل دان ملاوات"),
    (r"mix\s*[-–—]\s*n\s*[-–—]\s*match",
     "ڤادنکن ڤاسڠن"),
    (r"mix\s+and\s+match",
     "ڤادنکن ڤاسڠن"),
    (r"think\s*[-–— ]*\s*pair\s*[-–— ]*\s*share",
     "فيکير، برڤاسڠن دان برکوڠسي"),
    (r"personal\s+learning\s+experiences",
     "ڤڠالمن ڤريبادي"),
    (r"gallery\s+walk",
     "جلاجه ݢاليري"),
    (r"round\s+robin",
     "ڤرکوڠسين سچارا برݢيلير"),
    (r"shoulder\s+partner",
     "راکن سبله"),
    (r"face\s+partner",
     "راکن برهادڤن"),
    (r"talk\s+partners?",
     "ڤربينچڠن دڠن ڤاسڠن"),
    (r"rol+ing\s+chips?",
     "ڤرکوڠسين سچارا برݢيلير"),
    (r"role\s*[-–— ]\s*play",
     "لاكونن ڤرانن"),
    (r"hot\s+seat",
     "کروسي ڤانس"),
    (r"brainstorming",
     "سومبڠ سارن"),
    (r"the\s+yarn\s+yarn",
     "جالينن بنڠ"),
    (r"puzzle\s+it\s+out",
     "تيکاته-تيکي"),
    (r"talking\s+chips",
     "ݢيليرن برچاکڤ"),
    (r"round\s+table",
     "ڤربينچڠن ميجا بولت"),
    (r"recap\s+group",
     "اولڠ کاجي برکومڤولن"),
    (r"circle\s+time",
     "ماس بولتن"),
    (r"free\s+discussion",
     "ڤربينچڠن ببس"),
    (r"thumbs\s+up",
     "ايشارت ايبو جاري"),
    (r"game",
     "ڤرماينن"),
    # The official i-THINK method name is transliterated, not discarded.
    (r"i\s*[-–— ]\s*think",
     "اي-تينک"),
    (r"\bmatch\b",
     "ڤادنکن"),
)

_RULES = tuple(
    (re.compile(r"(?<![A-Za-z])(?:" + pattern + r")(?![A-Za-z])", re.I), jawi)
    for pattern, jawi in _REPLACEMENTS
)
_MARKER = "_cikgulaju_pi_jawi_english_terms_20261122"


def normalize_english_terms(text: str) -> str:
    """Replace named methods only, preserving all surrounding source text."""
    if not isinstance(text, str) or not text:
        return text
    for pattern, jawi in _RULES:
        text = pattern.sub(lambda _match, label=jawi: label, text)
    return text


def _pi_rph(state) -> bool:
    return (
        isinstance(state, dict)
        and state.get("subject") == "Pendidikan Islam"
        and state.get("task") == "rph"
    )


def prepare_pi_state(state: dict) -> dict:
    """Touch only activity/assessment presentation fields, never SK/SP.

    A read-only database row is copied before changing its display text.
    Every returned object retains the same lesson identity and ordering.
    """
    if not _pi_rph(state):
        return state
    for key in ("rpt_activity_note", "rpt_assessment_note"):
        if isinstance(state.get(key), str):
            state[key] = normalize_english_terms(state[key])
    for key in ("_quick_selected_rpt_row_v2388", "quick_rpt_row"):
        original = state.get(key)
        if isinstance(original, dict):
            changed = dict(original)
            for field in ("activity_note", "assessment_note"):
                if isinstance(changed.get(field), str):
                    changed[field] = normalize_english_terms(changed[field])
            state[key] = changed
    return state


def install(runtime) -> bool:
    """Install on the one native Telegram text generator (Web shares it)."""
    if getattr(runtime, _MARKER, False):
        return True
    original = getattr(runtime, "_local_rph_text", None)
    if not callable(original):
        return False

    @wraps(original)
    def _pi_jawi_terms(s):
        if not _pi_rph(s):
            return original(s)
        # Capture only the existing source activity/assessment notes.
        # Do not run a global replacement over the full RPH: that might
        # unintentionally alter a teacher's reflection, SK/SP or book title.
        source_notes = []
        for key in ("rpt_activity_note", "rpt_assessment_note"):
            if isinstance(s.get(key), str):
                source_notes.append(s[key])
        for key in ("_quick_selected_rpt_row_v2388", "quick_rpt_row"):
            row = s.get(key)
            if isinstance(row, dict):
                for field in ("activity_note", "assessment_note"):
                    if isinstance(row.get(field), str):
                        source_notes.append(row[field])
        prepare_pi_state(s)
        text = original(s)
        if isinstance(text, str):
            # A few historical generators directly copied the full
            # RPT note instead of the normalized display field.
            # Replace only that exact source-note block if it survives.
            for note in source_notes:
                revised = normalize_english_terms(note)
                if note != revised and note in text:
                    text = text.replace(note, revised)
        return text

    runtime._local_rph_text = _pi_jawi_terms
    setattr(runtime, _MARKER, True)
    return True
