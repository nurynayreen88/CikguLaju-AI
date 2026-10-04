

# ===== v25.247 ENGLISH Y4 VERIFIED WORKBOOK UNITS 5-10 ANCHORS =====
# Evidence-based additive extension; L67 corrected after SOW + visual Workbook cross-check.
_EN_WB_VERIFIED_Y4_V25247 = dict(globals().get('_EN_WB_VERIFIED_Y4_V25246', {}))
_EN_WB_VERIFIED_Y4_V25247.update({
 65:(39,38),66:(39,38),67:(40,39),80:(47,46),
 81:(50,49),82:(50,49),83:(51,50),87:(51,50),96:(56,55),
 113:(68,67),114:(68,67),129:(77,76),130:(77,76),144:(83,82),145:(86,85)
})
_v25247_book_pages_base = globals().get('_en_book_pages_v25232')
def _en_book_pages_v25232(ss,key):
    if key == 'activity' and _en_primary_v25232(ss):
        try:
            y=_english_primary_year_number_v2517((ss or {}).get('year'))
            lesson=int((ss or {}).get('lesson_no') or (ss or {}).get('lesson') or (ss or {}).get('textbook_lesson_no'))
            if y == 4:
                item=_EN_WB_VERIFIED_Y4_V25247.get(lesson)
                if item: return [int(item[0])]
        except Exception: pass
    if callable(_v25247_book_pages_base): return _v25247_book_pages_base(ss,key)
    return []
_v25247_physical_base = globals().get('_book_physical_page_v25237')
def _book_physical_page_v25237(ss,key,page):
    try:
        y=_english_primary_year_number_v2517((ss or {}).get('year'))
        if y == 4 and key == 'activity':
            lesson=int((ss or {}).get('lesson_no') or (ss or {}).get('lesson') or (ss or {}).get('textbook_lesson_no'))
            item=_EN_WB_VERIFIED_Y4_V25247.get(lesson)
            if item and int(page)==int(item[0]): return int(item[1])
    except Exception: pass
    if callable(_v25247_physical_base): return _v25247_physical_base(ss,key,page)
    return int(page)
APP_VERSION='v25.247-ENGLISH-Y4-WORKBOOK-ANCHORS-U5-U10'
# ===== END v25.247 =====
