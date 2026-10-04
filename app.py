

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

# v25.248 Y4 workbook verified gap-fill data
_EN_WB_VERIFIED_Y4_V25248 = dict(_EN_WB_VERIFIED_Y4_V25247)
_EN_WB_VERIFIED_Y4_V25248.update({68:(40,39),70:(41,40),71:(41,40),72:(43,42),73:(43,42),75:(45,44),76:(42,41),86:(51,50),88:(52,51),91:(52,51),92:(54,53),93:(55,54),94:(53,52),98:(59,58),99:(60,59),100:(60,59),102:(60,59),103:(60,59),104:(61,60),108:(62,61),110:(62,61),115:(69,68),116:(69,68),119:(69,68),120:(70,69),121:(70,69),126:(72,71),131:(78,77),134:(78,77),135:(78,77),136:(79,78),137:(79,78),139:(79,78),140:(80,79),142:(81,80),147:(87,86),148:(87,86),150:(87,86),152:(88,87),155:(88,87),156:(89,88),157:(91,90)})

# v25.248 activate Y4 verified Workbook gap-fill
_v25248_pages_base = _en_book_pages_v25232
def _en_book_pages_v25232(ss,key):
    if key == 'activity' and _en_primary_v25232(ss):
        try:
            y=_english_primary_year_number_v2517((ss or {}).get('year'))
            n=int((ss or {}).get('lesson_no') or (ss or {}).get('lesson') or (ss or {}).get('textbook_lesson_no'))
            if y == 4 and n in _EN_WB_VERIFIED_Y4_V25248: return [int(_EN_WB_VERIFIED_Y4_V25248[n][0])]
        except Exception: pass
    return _v25248_pages_base(ss,key) if callable(_v25248_pages_base) else []
_v25248_phys_base = _book_physical_page_v25237
def _book_physical_page_v25237(ss,key,page):
    try:
        y=_english_primary_year_number_v2517((ss or {}).get('year'))
        n=int((ss or {}).get('lesson_no') or (ss or {}).get('lesson') or (ss or {}).get('textbook_lesson_no'))
        if y == 4 and key == 'activity' and n in _EN_WB_VERIFIED_Y4_V25248:
            item=_EN_WB_VERIFIED_Y4_V25248[n]
            if int(page)==int(item[0]): return int(item[1])
    except Exception: pass
    return _v25248_phys_base(ss,key,page) if callable(_v25248_phys_base) else int(page)
APP_VERSION='v25.248-ENGLISH-Y4-WORKBOOK-U5-U10-GAP-FILL'
