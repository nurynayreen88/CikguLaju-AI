"""Restore proven truncated *display* steps from active, verified PI RPT.

The native 809+ PI source has the complete teaching note. A legacy row
formatter can emit only "1. first sentence 2." and repeat the same fragment
under Activity 2. This adapter restores the exact later steps without
inventing text, modifying the database, or touching SK/SP/reflection.

Runs at the final _rph_rows boundary shared by the existing Word/PDF
generators. Unknown patterns are left completely unchanged.
"""
from __future__ import annotations

import re
from functools import wraps

_STEP = re.compile(r"(?<!\S)([1-9])\.\s+(?=\S)")
_MARKER = "_CIKGULAJU_PI_VERIFIED_RPT_STEPS_RESTORED_20261123"


def _source_steps(note):
    if not isinstance(note, str) or len(note.strip()) < 70:
        return None
    text = note.strip()
    markers = list(_STEP.finditer(text))
    if len(markers) != 4 or [int(m.group(1)) for m in markers] != [1, 2, 3, 4]:
        return None
    if markers[0].start() != 0:
        return None
    steps = []
    for idx, match in enumerate(markers):
        end = markers[idx+1].start() if idx+1 < len(markers) else len(text)
        sentence = text[match.end():end].strip()
        if len(sentence) < 8 or not any("\u0600" <= ch <= "\u08ff" for ch in sentence):
            return None
        steps.append(sentence)
    return tuple(steps)


def restore_verified_pi_activity_rows(state, rows):
    """Return rows with all 4 source steps only for the exact proven truncation."""
    if not isinstance(state, dict) or not isinstance(rows, dict):
        return rows
    if state.get("subject") != "Pendidikan Islam" or state.get("task") != "rph":
        return rows
    master = state.get("_quick_selected_rpt_row_v2388")
    if not isinstance(master, dict):
        return rows
    if (str(master.get("id") or "") != str(state.get("rpt_entry_id") or "")
            or master.get("verified") not in (1, True)):
        return rows
    steps = _source_steps(master.get("activity_note"))
    if steps is None:
        return rows
    activity = rows.get("AKTIVITI UTAMA")
    if not isinstance(activity, str):
        return rows

    # Both occurrences must be proven exact partial *copies of source step 1*.
    # The trailing "2." is a chopped marker, NOT an extra standalone lesson
    # instruction. Never remove any valid numbered step or verse number.
    first_partial = "1. " + steps[0] + " 2."
    repeated_partial = "2. " + steps[0] + " 2."
    if activity.count(first_partial) != 1 or activity.count(repeated_partial) != 1:
        return rows
    if any(f"{number}. {step}" in activity
           for number, step in enumerate(steps[1:], 2)):
        # Already complete, or an unfamiliar partial revision: don't meddle.
        return rows

    restored = activity.replace(first_partial, "1. " + steps[0], 1)
    restored = restored.replace(
        repeated_partial,
        "\n".join(f"{i}. {step}" for i, step in enumerate(steps[1:], 2)),
        1,
    )
    if restored == activity or any(f"{i}. {step}" not in restored
                                   for i, step in enumerate(steps, 1)):
        return rows
    updated = dict(rows)
    updated["AKTIVITI UTAMA"] = restored
    return updated


def install(runtime):
    if getattr(runtime, _MARKER, False):
        return True
    old = getattr(runtime, "_rph_rows", None)
    if not callable(old):
        return False

    @wraps(old)
    def source_complete_pi_rows(state, source_text):
        original_rows = old(state, source_text)
        return restore_verified_pi_activity_rows(state, original_rows)

    runtime._rph_rows = source_complete_pi_rows
    setattr(runtime, _MARKER, True)
    return True
