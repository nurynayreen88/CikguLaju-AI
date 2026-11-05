"""English Year 5 fixed-SOW *draft preview* for native Telegram RPH Word/PDF.

151 verified *standard pairs* and lesson-number-matched markdown sources can
feed teacher-facing clearly labelled PROVISIONAL DRAFT lesson plans. This
is independent of release_approvals_2027.json: nothing is marked READY, and
the existing final-release sign-off/checksum gate is NEVER bypassed.
Nine teacher-choice Lessons are handled by their own proposal adapter.
"""
from pathlib import Path
import re

from web.english_y5_standalone_runtime import (
    _target, _gate, load_lesson, adapt_rows as _stage_rows,
    approved_for_telegram, LESSON_ROOT, CHOICE_LESSONS,
)

_LS = re.compile(r"(?<!\d)[1-5]\.\d\.\d(?!\d)")
_BAD_QA = re.compile(r"(?i)(?:NOT READY|QA status|source verification pending|"
                     r"internal audit|do not publish|incomplete QA)")


def _success_evidence(number, root):
    """Use a source-authored success criterion or PBD evidence, never fabricate."""
    path = Path(root) / ("lesson_%03d.md" % number)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    for field in ("Success criteria", "Success criterion", "Success evidence", "PBD evidence"):
        match = re.search(r"(?im)^\s*(?:\*\*)?" + re.escape(field) +
                          r"(?:\*\*)?\s*:\s*([^\r\n]+)", text)
        if not match:
            continue
        content = re.sub(r"\*\*([^*]+)\*\*", r"\1", match.group(1)).strip()
        if content and not _BAD_QA.search(content):
            return content
    return None


def preview_rows(state, rows, *, root=LESSON_ROOT):
    number = _target(state)
    if number is None or number in CHOICE_LESSONS or not isinstance(rows, dict):
        return rows
    if state.get("task") and str(state.get("task")).strip().casefold() != "rph":
        return rows
    sow = _gate(root)
    if not isinstance(sow, dict):
        return rows
    expected = sow.get(str(number))
    if not isinstance(expected, dict) or expected.get("teacher_choice") is not False:
        return rows
    main, comp = expected.get("main_ls"), expected.get("complementary_ls")
    if not isinstance(main, str) or not isinstance(comp, str):
        return rows
    if not _LS.fullmatch(main) or not _LS.fullmatch(comp):
        return rows
    for field, exact in (("sp_code", main),
                         ("bi_main_sp_code", main),
                         ("comp_sp_code", comp),
                         ("bi_comp_sp_code", comp)):
        selected = str(state.get(field) or "").strip()
        if selected and selected != exact:
            return rows
    lesson = load_lesson(number, root=root)
    if lesson is None or not {main, comp}.issubset(lesson["source_codes"]):
        return rows
    staged = _stage_rows(state, rows, root=root)
    if staged is rows:
        return rows
    for key in ("SET INDUKSI", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP",
                "OBJEKTIF PEMBELAJARAN", "BAHAN BANTU MENGAJAR"):
        if not isinstance(staged.get(key), str) or not staged[key].strip():
            return rows
        if _BAD_QA.search(staged[key]):
            return rows
    # Explicitly distinguish a source-backed, classroom-useful draft from
    # a teacher-approved final RPH. Source page/audio verification is pending.
    result = dict(staged)
    result["TAJUK"] = "CADANGAN CIKGULAJU (DRAF) — %s — %s" % (
        str(expected.get("topic") or "").strip(),
        str(expected.get("focus") or "").strip())
    result["MAIN CONTENT STANDARD"] = main.rsplit(".", 1)[0]
    result["MAIN LEARNING STANDARD"] = main
    result["COMPLEMENTARY CONTENT STANDARD"] = comp.rsplit(".", 1)[0]
    result["COMPLEMENTARY LEARNING STANDARD"] = comp
    evidence = _success_evidence(number, root)
    if evidence:
        result["KRITERIA KEJAYAAN"] = evidence
    # The fixed standard pair is sourced from the official lesson table,
    # but this alone does not approve printed-page references/audio.
    return result


def install(runtime):
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y5_FIXED_DRAFT_PREVIEW_ACTIVE", False):
        return True
    old = getattr(runtime, "_rph_rows", None)
    if not callable(old):
        return False

    def year5_fixed_preview(state, *args, **kwargs):
        original = old(state, *args, **kwargs)
        try:
            number = _target(state)
            # If a lesson is truly finally approved, preserve its separately
            # audited release route rather than overprinting a DRAFT label.
            if number is None or number in CHOICE_LESSONS or approved_for_telegram(number):
                return original
            return preview_rows(state, original)
        except Exception as exc:
            print("English Y5 fixed draft preview fallback:", repr(exc), flush=True)
            return original

    runtime._rph_rows = year5_fixed_preview
    runtime.CIKGULAJU_ENGLISH_Y5_FIXED_DRAFT_PREVIEW_ACTIVE = True
    return True
