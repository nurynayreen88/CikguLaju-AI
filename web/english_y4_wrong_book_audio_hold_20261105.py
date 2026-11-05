"""Protect Year4 Get Smart Plus 4 from Super Minds 1 audio sent by legacy routes.

Source evidence: audits/english_y4_wrong_book_audio_hold_manifest_20261105.json
24 WMA file IDs / 19 Y4 Lessons occur in a folder nested within
'Super Minds 1 Audio Unzipped'. They must NEVER be used as Get Smart Plus 4
audio, regardless of matching disc/track numerals.

Fail closed on those 19 Year4 Lessons' media pickers, selected-material
sends, and old direct media callbacks until independently verified correct
Get Smart Plus 4 files are installed. Other years/subjects, RPH Word/PDF,
users, payments, credits and databases are unchanged.
"""
import re

HOLD_LESSONS=frozenset((
    7,8,9,11,12,17,22,24,29,32,48,59,97,98,99,102,103,107,110
))

def _risk(state):
    if not isinstance(state,dict):
        return False
    if str(state.get("subject") or "").strip().casefold() not in ("english","bahasa inggeris"):
        return False
    year=str(state.get("year") or state.get("grade") or "").strip().casefold()
    if re.fullmatch(r"(?:(?:year|tahun)\s*)?0?4",year) is None:
        return False
    value=state.get("lesson_no") or state.get("textbook_lesson_no") or state.get("lesson")
    try:
        return int(value) in HOLD_LESSONS
    except (TypeError,ValueError,OverflowError):
        return False

def install(runtime):
    if getattr(runtime,"CIKGULAJU_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE",False):
        return True
    available=getattr(runtime,"_available_materials_v2528",None)
    sender=getattr(runtime,"_send_reference_material_v2528",None)
    if not callable(available) or not callable(sender):
        return False
    direct=getattr(runtime,"_send_reference_material",None)
    notice=getattr(runtime,"send",None)

    # Existing historical maps are in-memory dictionaries only, not DB rows.
    # Remove only 19 unsafe Year4 lesson entries. Other lesson maps remain.
    for name in ("_EN4_AUDIO_ALL_V25257","_EN4_AUDIO_ALL_V25258","_EN4_AUDIO_ALL_V25259"):
        mapping=getattr(runtime,name,None)
        if isinstance(mapping,dict):
            for n in HOLD_LESSONS:
                for key in (n,str(n),f"{n:03d}"):
                    mapping.pop(key,None)

    def _materials(ss,*args,**kwargs):
        keys=list(available(ss,*args,**kwargs) or [])
        if not _risk(ss):
            return keys
        ss.pop("audio_storage_file_id",None)
        ss["audio_status"]="WRONG_BOOK_SUPER_MINDS1_YEAR4_MEDIA_HOLD"
        ss["audio_reference"]="Get Smart Plus 4 audio pending verification"
        return [key for key in keys if key!="media"]

    def _hold(cid):
        if callable(notice):
            try:
                notice(cid,"🔊 Audio Lesson ini sedang dibetulkan. Fail lama "
                           "berasal daripada buku teks yang berbeza. "
                           "RPH, Buku Teks dan Workbook masih boleh digunakan.")
            except Exception:
                pass
        return False

    def _selected(cid,ss,key,*args,**kwargs):
        if key=="media" and _risk(ss):
            return _hold(cid)
        return sender(cid,ss,key,*args,**kwargs)

    runtime._available_materials_v2528=_materials
    runtime._send_reference_material_v2528=_selected

    if callable(direct):
        def _old(cid,ss,key,*args,**kwargs):
            if key=="media" and _risk(ss):
                return _hold(cid)
            return direct(cid,ss,key,*args,**kwargs)
        runtime._send_reference_material=_old

    runtime.CIKGULAJU_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE=True
    return True
