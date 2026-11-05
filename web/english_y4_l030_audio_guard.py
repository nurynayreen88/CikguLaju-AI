"""Source-locked Telegram media routing for English Year 4 Lesson 030/103.

Teacher confirmed on 5 November 2026 that Get Smart Plus 4 Student's Book
p.20 Activity 2 uses CD1 Track 29, as Teacher's Book p.39 indicates, not
CD2 Track 29 as printed in the SOW. Route only the exact CD1 MP3 Drive ID.
Remove stale CD2 mapping and never delegate L030 audio to legacy senders.
The code-level source mapping is confirmed; actual Telegram delivery remains
unverified until a real authorized user test.

For Lesson 103 keep only CD2 Track 26 (TB p.111), not Track 27/28.
No other lessons, databases, quotas or billing are modified.
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
    if not re.fullmatch(r"(?:(?:year|tahun)\s*)?0?4", year):
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

            # TB p.111: Lesson 103 Activity 5 uses CD2 Track 26 only.
            # TB p.112: CD2 Tracks 27/28 are Lesson 104 activities, but
            # the historical v25.258/259 map erroneously attached both
            # to Lesson 103. Do not move them into Lesson 104 before
            # independently checking content and end-user delivery.
            for key in (103, "103"):
                if key in mapping:
                    mapping[key] = [
                        row for row in mapping[key]
                        if isinstance(row, dict)
                        and row.get("audio_reference") == "CD2 Track 26"
                        and row.get("storage_file_id")
                            == "1vpNkB4OWao5iPQvHzEpemQrlNiNhkX4H"
                    ]

    # Exact, source-confirmed Drive asset. The underlying sender downloads the
    # MP3 directly and sends it via Telegram; never reuse CD2 Track 29.
    approved = {
        "audio_reference": "CD1 Track 29",
        "storage_file_id": "15tyBPsUwd5z9AknoOOUIiaTN6QT-Xrct",
        "title": "English Year 4 • Lesson 30 • CD1 Track 29",
        "verified": 1,
    }
    verified_sender = getattr(runtime, "_send_verified_media_rows_v2594", None)
    notice = getattr(runtime, "send", None)

    def _source_confirmed_media(ss, *args, **kwargs):
        keys = list(available(ss, *args, **kwargs) or [])
        if not _is_y4_l030(ss):
            return keys
        # The prior provider may have injected the CD2 ID into the state.
        ss.pop("audio_storage_file_id", None)
        ss["audio_reference"] = approved["audio_reference"]
        if not callable(verified_sender):
            ss["audio_status"] = "CD1_MAPPING_CONFIRMED_SEND_NOT_AVAILABLE"
            return [key for key in keys if key != "media"]
        ss["audio_status"] = "CD1_SOURCE_CONFIRMED_DELIVERY_UNTESTED"
        ss["audio_storage_file_id"] = approved["storage_file_id"]
        if "media" not in keys:
            keys.append("media")
        return keys

    def _blocked_audio_message(cid):
        if callable(notice):
            try:
                notice(cid, "🔊 Audio English Year 4 Lesson 30 belum boleh dihantar "
                       "kerana penghantar audio yang disahkan tidak tersedia. "
                       "Sila gunakan rujukan CD1 Track 29 Student's Book m/s 20.")
            except Exception:
                pass
        return False

    def _send_cd1_only(cid):
        if not callable(verified_sender):
            return _blocked_audio_message(cid)
        try:
            return bool(verified_sender(cid, [dict(approved)]))
        except Exception as exc:
            print("English Y4 L030 CD1 media delivery failed:", repr(exc), flush=True)
            return False

    def _safe_send(cid, ss, key, *args, **kwargs):
        if key == "media" and _is_y4_l030(ss):
            return _send_cd1_only(cid)
        return sender(cid, ss, key, *args, **kwargs)

    runtime._available_materials_v2528 = _source_confirmed_media
    runtime._send_reference_material_v2528 = _safe_send

    # The legacy direct sender bypasses the material picker; guard it too.
    direct = getattr(runtime, "_send_reference_material", None)
    if callable(direct):
        def _safe_direct(cid, ss, key, *args, **kwargs):
            if _is_y4_l030(ss):
                if key == "media":
                    return _send_cd1_only(cid)
                return _safe_send(cid, ss, key, *args, **kwargs)
            return direct(cid, ss, key, *args, **kwargs)
        runtime._send_reference_material = _safe_direct

    runtime.CIKGULAJU_Y4_L030_AUDIO_CONFLICT_GUARD_ACTIVE = True
    return True
