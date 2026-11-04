"""Fail-closed Telegram media guard for English Year 4 Lesson 030.

Original TB p.39 assigns SB p.20 Activity 2 to CD1 Track29, but the
official SOW prints CD2 Track29. Existing app.py v25.257/258/259 media
maps contain a CD2 file for L030; its spoken content is not independently
verified. Hide only this one lesson's media and reject stale media buttons
until the audio-content and teacher-delivery release gates are approved.

No DB writes, credit changes, entitlement changes, or media sends.
"""
import re


def _is_y4_l030(ss):
    if not isinstance(ss, dict):
        return False
    if str(ss.get("subject") or "").strip().casefold() not in (
        "english", "bahasa inggeris"
    ):
        return False
    year = str(ss.get("year") or ss.get("grade") or "").strip().casefold()
    if not re.fullmatch(r"(?:(?:year|tahun)\\s*)?0?4", year):
        return False
    raw_lesson = ss.get("lesson_no") or ss.get("textbook_lesson_no") or ss.get("lesson")
    try:
        return int(raw_lesson) == 30
    except (ValueError, TypeError, OverflowError):
        return False


def install(runtime):
    """Remove stale CD2 mapping and guard both picker and send functions.

    Install last, after other runtime adapters have wrapped these functions.
    """
    if getattr(runtime, "CIKGULAJU_Y4_L030_AUDIO_CONFLICT_GUARD_ACTIVE", False):
        return True
    available = getattr(runtime, "_available_materials_v2528", None)
    sender = getattr(runtime, "_send_reference_material_v2528", None)
    if not callable(available) or not callable(sender):
        return False

    # Remove stale 'verified' CD2 Track29 rows only for Lesson 30.
    # Retain every other lesson's existing audio data and delivery method.
    for name in (
        "_EN4_AUDIO_ALL_V25257",
        "_EN4_AUDIO_ALL_V25258",
        "_EN4_AUDIO_ALL_V25259",
    ):
        mapping = getattr(runtime, name, None)
        if isinstance(mapping, dict):
            for key in (30, "30", "030"):
                mapping.pop(key, None)

    notice = getattr(runtime, "send", None)

    def _hide_conflicting_media(ss, *args, **kwargs):
        keys = list(available(ss, *args, **kwargs) or [])
        if not _is_y4_l030(ss):
            return keys
        # The legacy media layer may have left a stale verified flag.
        ss["audio_status"] = "SOURCE_CONFLICT_NOT_VERIFIED"
        ss["audio_reference"] = "TB CD1 Track29 / SOW CD2 Track29 — pending content QA"
        ss.pop("audio_storage_file_id", None)
        return [key for key in keys if key != "media"]

    def _blocked_audio_message(cid):
        if callable(notice):
            try:
                notice(cid, "🔊 Audio English Year 4 Lesson 30 ditangguhkan sementara "
                       "kerana rujukan Teacher's Book dan SOW bercanggah. "
                       "RPH Word/PDF masih boleh digunakan.")
            except Exception:
                pass
        return False

    def _safe_send(cid, ss, key, *args, **kwargs):
        if key == "media" and _is_y4_l030(ss):
            return _blocked_audio_message(cid)
        return sender(cid, ss, key, *args, **kwargs)

    runtime._available_materials_v2528 = _hide_conflicting_media
    runtime._send_reference_material_v2528 = _safe_send

    # Legacy direct sender v25.259 bypassed the normal media selector.
    # Safeguard that alternative path, including stale callback selections.
    direct = getattr(runtime, "_send_reference_material", None)
    if callable(direct):
        def _safe_direct(cid, ss, key, *args, **kwargs):
            if _is_y4_l030(ss):
                if key == "media":
                    return _blocked_audio_message(cid)
                return _safe_send(cid, ss, key, *args, **kwargs)
            return direct(cid, ss, key, *args, **kwargs)
        runtime._send_reference_material = _safe_direct

    runtime.CIKGULAJU_Y4_L030_AUDIO_CONFLICT_GUARD_ACTIVE = True
    return True
