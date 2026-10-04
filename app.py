

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


# ===== v25.249 ENGLISH Y4 VERIFIED LITERATURE RESOURCES =====
# Additive metadata resolver. Workbook/SB/TB page resolvers remain unchanged.
_EN4_LIT_V25249 = {
5:("Holiday Memories","Poetry","7, 8-11, 13, 14",""),
10:("At the Playground","Poetry","26, 27, 30, 31",""),
15:("Sounds like Magic","Poetry","38, 40",""),
21:("Grandma's House","Poetry","46, 47, 55",""),
26:("Clap your hands","Poetry","59, 60",""),
31:("Noisy Food","Poetry","65, 67-70",""),
37:("Woodpecker","Poetry","75, 79",""),
42:("Sand Castle","Poetry","85, 86-89, 96-97",""),
47:("The King of Kites","Short Story","70-73","book cover / prediction"),
53:("The King of Kites","Short Story","9-10","kite-making and sewing vocabulary"),
58:("The King of Kites","Short Story","28, 30","events / sequencing"),
63:("The King of Kites","Short Story","38-39","character adjectives"),
69:("The King of Kites","Short Story","80-81","feelings / adjectives"),
74:("The King of Kites","Short Story","41-44","setting / creative response"),
79:("The King of Kites","Short Story","52-53","values / advice"),
85:("The King of Kites","Short Story","56","values"),
90:("The King of Kites","Short Story","66","invitation / congratulatory card"),
95:("The King of Kites","Short Story","60, 62-64","encouragement / role play"),
101:("The Jungle Book","Graphic Novel","27",""),
106:("The Jungle Book","Graphic Novel","6-12","features / Chapters 1-2"),
111:("The Jungle Book","Graphic Novel","35-36","Chapters 3-4 / sequence"),
117:("The Jungle Book","Graphic Novel","33-34, 63","Chapter 5 / feelings"),
122:("The Jungle Book","Graphic Novel","48",""),
127:("The Jungle Book","Graphic Novel","62","verbs / jazz chant"),
133:("The Jungle Book","Graphic Novel","63","The Red Flower"),
138:("The Jungle Book","Graphic Novel","68-69, 128","Shere Khan / creative response / assessment"),
143:("The Jungle Book","Graphic Novel","70","Akela's death / poem"),
149:("The Jungle Book","Graphic Novel","73","Mowgli: jungle or village"),
154:("The Jungle Book","Graphic Novel","77","characters / values"),
159:("The Jungle Book","Graphic Novel","84-88, 128","Readers' Theatre / assessment"),
}
def _en_y4_literature_resource_v25249(ss):
    try:
        y=_english_primary_year_number_v2517((ss or {}).get('year'))
        n=int((ss or {}).get('lesson_no') or (ss or {}).get('lesson') or (ss or {}).get('textbook_lesson_no'))
        if y != 4 or n not in _EN4_LIT_V25249: return None
        title,kind,pages,focus=_EN4_LIT_V25249[n]
        return {"lesson":n,"title":title,"type":kind,"guide_pages":pages,"focus":focus,"source":"CCL Teaching Guidebook (BPK)"}
    except Exception:
        return None
APP_VERSION='v25.249-ENGLISH-Y4-LITERATURE-30-VERIFIED'
# ===== END v25.249 =====


# ===== v25.250 ENGLISH Y4 LITERATURE DOWNLOAD SOURCES =====
# Verified Drive assets in the same Year 4 resource folder. Additive only.
_EN4_LIT_SOURCE_V25250 = {
 "Poetry":{"name":"Anthology of Poems.pdf","drive_id":"1-GGW14NGcz7Eaii9JUJEofRsWd0YO0Hx"},
 "Short Story":{"name":"The King of Kites YEAR 4.pdf","drive_id":"1AAR6_6hoQkkl8U73b6MNXKA2ZEW-g8eU"},
 "Graphic Novel":{"name":"The Jungle Book YEAR 4.pdf","drive_id":"1oeQo76j1GUbo7hdBQK09g4QrN2dd7FsC"},
}
_v25250_lit_base = _en_y4_literature_resource_v25249
def _en_y4_literature_resource_v25249(ss):
    item=_v25250_lit_base(ss) if callable(_v25250_lit_base) else None
    if not item: return item
    src=_EN4_LIT_SOURCE_V25250.get(item.get("type"))
    if src:
        item=dict(item)
        item["resource_name"]=src["name"]
        item["drive_id"]=src["drive_id"]
        item["drive_view_url"]="https://drive.google.com/file/d/%s/view" % src["drive_id"]
    return item
APP_VERSION='v25.250-ENGLISH-Y4-LITERATURE-DOWNLOAD-SOURCES'
# ===== END v25.250 =====


# ===== v25.251 ENGLISH Y4 WORKBOOK CROSS-VERIFIED ADDITIONS =====
_EN_WB_VERIFIED_Y4_V25251 = dict(_EN_WB_VERIFIED_Y4_V25248)
_EN_WB_VERIFIED_Y4_V25251.update({105:(61,60),107:(64,63),125:(73,72),141:(82,81)})
_v25251_pages_base = _en_book_pages_v25232
def _en_book_pages_v25232(ss,key):
    if key == 'activity' and _en_primary_v25232(ss):
        try:
            y=_english_primary_year_number_v2517((ss or {}).get('year'))
            n=int((ss or {}).get('lesson_no') or (ss or {}).get('lesson') or (ss or {}).get('textbook_lesson_no'))
            if y == 4 and n in _EN_WB_VERIFIED_Y4_V25251: return [int(_EN_WB_VERIFIED_Y4_V25251[n][0])]
        except Exception: pass
    return _v25251_pages_base(ss,key) if callable(_v25251_pages_base) else []
_v25251_phys_base = _book_physical_page_v25237
def _book_physical_page_v25237(ss,key,page):
    try:
        y=_english_primary_year_number_v2517((ss or {}).get('year'))
        n=int((ss or {}).get('lesson_no') or (ss or {}).get('lesson') or (ss or {}).get('textbook_lesson_no'))
        if y == 4 and key == 'activity' and n in _EN_WB_VERIFIED_Y4_V25251:
            item=_EN_WB_VERIFIED_Y4_V25251[n]
            if int(page)==int(item[0]): return int(item[1])
    except Exception: pass
    return _v25251_phys_base(ss,key,page) if callable(_v25251_phys_base) else int(page)
APP_VERSION='v25.251-ENGLISH-Y4-WORKBOOK-CROSS-VERIFIED'
# ===== END v25.251 =====


# ===== v25.252 ENGLISH Y4 COMPLETE RESOURCE COVERAGE =====
# Explicit fallback for the 23 verified Year 4 lessons which intentionally have no WB page.
_EN4_NON_WB_V25252 = {
1:("SB/TB + audio","Activity 1; TB p.18; CD1 Track 3; flag flashcards"),
4:("SOW/custom","Non-textbook writing; teacher worksheet or pupil-made materials"),
11:("SB/TB + audio/phonics","SB pp.12-13; Track 16; Phonics 1 TB p.98"),
12:("SB/TB + audio","Revision/Activity 1 TB p.30; Track 17; SB p.14 cards"),
13:("SB/TB","SB p.11 email; Activities 1-2 TB p.26; Track 15"),
23:("SOW/custom","Timetable speaking/writing; timetable and paper strips"),
29:("SB/TB + audio/CLIL","Social Studies CLIL 1; SB p.129; TB p.193; Tracks 35-36; dictionaries"),
39:("SOW/custom","Past simple review; teacher-selected materials"),
43:("SB/TB + audio/phonics","Phonics 3; SB p.121; TB pp.177-178; CD3 Tracks 10-11"),
44:("SOW/custom","Historical figures narration; teacher-prepared materials"),
45:("SB/TB + teacher worksheet","SB p.32; TB pp.54-55; Track 47; Egypt sentence worksheet"),
46:("SB/TB + digital/email","SB p.33; TB p.56; Track 49; email writing"),
77:("SB/TB + teacher worksheet","Eating right supplementary reading/vocabulary matching"),
78:("SOW/custom project","Healthy-food poster project"),
84:("SB/TB + project material","Famous-building pictures/planning"),
89:("SOW/custom continuation","Famous-building writing continuation from L84"),
109:("SB/TB/SOW","Helping out reading; no verified Workbook page"),
118:("SOW/custom listening","Malaysia endangered animals; pictures/listening/worksheet"),
123:("SB/TB + phonics/dictionaries","Amazing animals pronunciation/reading extension"),
132:("SOW/custom writing","Activities-day invitation/report"),
151:("SOW/custom speaking","Should/shouldn't learning-English lesson"),
153:("SOW/custom poster","Health poster"),
160:("Project-Based Learning","Teacher-selected topic/theme/skills/materials"),
}
def _en_y4_non_wb_resource_v25252(ss):
    try:
        y=_english_primary_year_number_v2517((ss or {}).get('year'))
        n=int((ss or {}).get('lesson_no') or (ss or {}).get('lesson') or (ss or {}).get('textbook_lesson_no'))
        if y != 4 or n not in _EN4_NON_WB_V25252: return None
        kind,detail=_EN4_NON_WB_V25252[n]
        return {"lesson":n,"resource_type":kind,"detail":detail,"workbook_expected":False}
    except Exception:
        return None
APP_VERSION='v25.252-ENGLISH-Y4-RESOURCE-COVERAGE-160'
# ===== END v25.252 =====
