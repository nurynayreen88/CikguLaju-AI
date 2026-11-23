"""Native RPH reflection linked to a *real* lesson objective/success criterion.

Presentation only: this operates at final _rph_rows for Word and PDF; never
edits verified RPT/DSKP fields, source text, activity steps or the master DB.
A teacher-written reflection or already specific reflection wins.

No student outcome is fabricated: the blank count is for the teacher to fill
after class. Only exact supported KSSR native subjects are in scope. Unknown
formats, Arabic, DLP/PPKI and reviewed independent renderers fail closed.
"""
from __future__ import annotations

import re
from functools import wraps

_MARKER = "_CIKGULAJU_OBJECTIVE_LINKED_RPH_REFLECTION_20261123"

# Other approved formats (DLP, PPKI, SJKC/SJKT, BA) require their own
# reviewed source and font testing. Scope first to ordinary KSSR native RPH.
_MALAY_SUBJECTS = frozenset({
    "bahasa melayu", "matematik", "sains", "pendidikan moral",
    "pendidikan muzik", "sejarah", "pendidikan seni visual",
    "reka bentuk dan teknologi",
    "pendidikan jasmani dan pendidikan kesihatan",
})
_ENGLISH_SUBJECTS = frozenset({"english", "bahasa inggeris"})
_PI_SUBJECTS = frozenset({"pendidikan islam"})

_GENERIC_CRITERIA = (
    "fokus pembelajaran", "fokus pdp", "objektif pembelajaran",
    "mengikut sp", "mengikut standard", "menunjukkan penguasaan terhadap",
    "menunjukkan penguasaan terhadap fokus",
    "موريد داڤت منيرو، منونجوقکن اتاو مڽلسايکن توݢسن",
    "فوکوس ڤدڤ",
)
_GENERIC_REFLECTION = (
    "mencapai objektif", "mencapai kriteria kejayaan",
    "belum mencapai objektif", "murid menguasai objektif",
    "pupils achieved the lesson objectives", "pupils achieved",
    "pupils met the lesson objectives", "require further support",
    "موريد منچاپاي اوبجيکتيف", "موريد ممرلوکن بيمبيڠن",
    "pd p dilaksanakan", "pdp dilaksanakan", "pd p berjalan",
)


def _language(state):
    if not isinstance(state, dict) or state.get("task") != "rph":
        return None
    for key in ("curriculum", "stream", "programme", "program",
                "school_type", "curriculum_version"):
        token = str(state.get(key) or "").casefold()
        if any(bad in token for bad in ("ppki", "dlp", "sjkc", "sjkt", "kp2027")):
            return None
    subject = " ".join(str(state.get("subject") or "").strip().casefold().split())
    if subject in _PI_SUBJECTS:
        return "jawi"
    if subject in _ENGLISH_SUBJECTS:
        return "en"
    if subject in _MALAY_SUBJECTS:
        return "ms"
    return None


def _generic_reflection(value):
    if not isinstance(value, str) or not value.strip():
        return True
    s = " ".join(value.casefold().split())
    return any(pattern in s for pattern in _GENERIC_REFLECTION)


def _focus(rows, language):
    # PI source success criterion is often stock scaffolding; use its verified
    # objective (e.g. named surah and ayat range) instead of that generic line.
    keys = ("OBJEKTIF PEMBELAJARAN", "KRITERIA KEJAYAAN") if language == "jawi" else (
        "KRITERIA KEJAYAAN", "OBJEKTIF PEMBELAJARAN")
    for key in keys:
        raw = rows.get(key)
        if not isinstance(raw, str):
            continue
        # At most ONE complete source line; never cut a source sentence in half.
        value = next((x.strip(" \t•-") for x in raw.splitlines() if x.strip()), "")
        value = " ".join(value.split())
        if not 23 <= len(value) <= 140 or any(x in value for x in ("____", "______")):
            continue
        if any(q in value.casefold() for q in _GENERIC_CRITERIA):
            continue
        if language == "jawi":
            if not any("\u0600" <= ch <= "\u08ff" for ch in value):
                continue
            value = re.sub(r"^موريد\s+داڤت\s*:\s*", "", value).strip()
            if not any("\u0600" <= ch <= "\u08ff" for ch in value):
                continue
        elif language == "en":
            if not re.search(r"[A-Za-z]{4,}", value):
                continue
        elif not re.search(r"[A-Za-z]{4,}", value):
            continue
        return value.rstrip(".؛;، ").strip()
    return None


def objective_linked_reflection(state, rows):
    """Return a row copy only where a generic reflection has real lesson evidence."""
    if not isinstance(rows, dict):
        return rows
    language = _language(state)
    if language is None:
        return rows
    # Manual teacher input is authoritative; never replace or paraphrase.
    if str(state.get("rph_teacher_reflection") or "").strip():
        return rows
    if str(state.get("rph_reflection_mode") or "").casefold() == "manual":
        return rows
    current = rows.get("REFLEKSI")
    if current is not None and not _generic_reflection(current):
        return rows
    evidence = _focus(rows, language)
    if not evidence:
        return rows
    if language == "jawi":
        generated = (
            "____ / ____ موريد منچاپاي ساسرن: " + evidence +
            ". موريد يڠ بلوم مڠواساءي دبمبيڠ سمولا."
        )
    elif language == "en":
        generated = (
            "____ / ____ pupils met the criterion: " + evidence +
            ". Others receive focused support."
        )
    else:
        generated = (
            "____ / ____ murid: " + evidence +
            ". Baki dibimbing semula."
        )
    # Preserve a compact one-paragraph footer and limit added page pressure.
    if len(generated) > 215 or (current and len(generated) > len(current) + 90):
        return rows
    revised = dict(rows)
    revised["REFLEKSI"] = generated
    return revised


def install(runtime):
    if getattr(runtime, _MARKER, False):
        return True
    previous = getattr(runtime, "_rph_rows", None)
    if not callable(previous):
        return False

    @wraps(previous)
    def linked_rows(state, *args, **kwargs):
        rows = previous(state, *args, **kwargs)
        return objective_linked_reflection(state, rows)

    runtime._rph_rows = linked_rows
    setattr(runtime, _MARKER, True)
    return True
