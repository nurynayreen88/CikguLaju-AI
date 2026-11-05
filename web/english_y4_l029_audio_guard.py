"""Fail-closed legacy audio delivery for English Year4 Lesson29 CLIL1.

Original Get Smart Plus 4 TB p193 and SB p129 require Class CD3
Tracks 35/36. Legacy v25.258/259 maps send CD1 WMA tracks 35/36
instead (and mislabel them as MP3). Remove only the incorrect Lesson29
media paths until exact CD3 files and normal-user Telegram delivery
are verified. Never change other lessons, credits, DB or RPH Word/PDF.
"""
import re


def _is_english_y4_l29(state):
    if not isinstance(state, dict):
        return False
    if str(state.get("subject") or "").strip().casefold() not in ("english","bahasa inggeris"):
        return False
    grade=str(state.get("year") or state.get("grade") or "").strip().casefold()
    if not re.fullmatch(r"(?:(?:year|tahun)\s*)?0?4",grade):
        return False
    raw=state.get("lesson_no") or state.get("textbook_lesson_no") or state.get("lesson")
    try:
        return int(raw)==29
    except (TypeError,ValueError,OverflowError):
        return False


def install(runtime):
    if getattr(runtime,"CIKGULAJU_Y4_L029_CLIL3_AUDIO_HOLD_ACTIVE",False):
        return True
    available=getattr(runtime,"_available_materials_v2528",None)
    sender=getattr(runtime,"_send_reference_material_v2528",None)
    if not callable(available) or not callable(sender):
        return False

    # No other lesson or source file is changed. Preserve the original map
    # elsewhere in GitHub for evidence; mutate only the live in-memory L29
    # entries that are known to refer to the wrong disc.
    for name in ("_EN4_AUDIO_ALL_V25258","_EN4_AUDIO_ALL_V25259"):
        mapping=getattr(runtime,name,None)
        if isinstance(mapping,dict):
            for lesson_key in (29,"29","029"):
                mapping.pop(lesson_key,None)

    notice=getattr(runtime,"send",None)

    def _safe_available(ss,*args,**kwargs):
        keys=list(available(ss,*args,**kwargs) or [])
        if not _is_english_y4_l29(ss):
            return keys
        ss.pop("audio_storage_file_id",None)
        ss["audio_reference"]="TB p.193: CD3 Tracks 35/36 (delivery pending)"
        ss["audio_status"]="CLIL_CD3_CONFIRMED_TELEGRAM_DELIVERY_PENDING"
        return [key for key in keys if key!="media"]

    def _hold(cid):
        if callable(notice):
            try:
                notice(cid,"🔊 Audio English Year 4 Lesson 29 ditangguhkan. "
                       "Teacher's Book m/s 193 menggunakan CD3 Track 35/36, "
                       "bukan CD1. RPH Word/PDF dan bahan lain tidak disekat.")
            except Exception:
                pass
        return False

    def _safe_send(cid,ss,key,*args,**kwargs):
        if key=="media" and _is_english_y4_l29(ss):
            return _hold(cid)
        return sender(cid,ss,key,*args,**kwargs)

    runtime._available_materials_v2528=_safe_available
    runtime._send_reference_material_v2528=_safe_send

    # A separate legacy direct route bypasses the material picker.
    direct=getattr(runtime,"_send_reference_material",None)
    if callable(direct):
        def _safe_direct(cid,ss,key,*args,**kwargs):
            if key=="media" and _is_english_y4_l29(ss):
                return _hold(cid)
            return direct(cid,ss,key,*args,**kwargs)
        runtime._send_reference_material=_safe_direct

    runtime.CIKGULAJU_Y4_L029_CLIL3_AUDIO_HOLD_ACTIVE=True
    return True
