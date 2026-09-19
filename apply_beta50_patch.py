from pathlib import Path

P=Path(__file__).with_name("app.py")
s=P.read_text(encoding="utf-8")
MARK="# BETA50_LESSON_FIRST_QA16"

# Runtime core is already a Git-safe 24,485,888-byte DB in the repository.
s=s.replace(
    "os.path.join(os.path.dirname(__file__), 'CikguLaju_Curriculum_Master_v1.db')",
    "os.path.join(os.path.dirname(__file__), 'CikguLaju_Curriculum_Master_v24_95_CORE.db')"
)

block=r'''
# BETA50_LESSON_FIRST_QA16
def _beta50_rpt_units(year_label, subject):
    """Verified RPT/SOW units available for lesson-first Beta flow."""
    con=_db()
    try:
        rows=con.execute("""SELECT id,sequence_no,unit_code,unit_title,topic,theme,skill_focus
                            FROM rpt_entries
                            WHERE year_label=? AND subject=? AND verified=1
                              AND content_verified=1 AND sequence_verified=1
                            ORDER BY sequence_no,id""",(year_label,subject)).fetchall()
        out=[]; seen=set()
        for r in rows:
            d=dict(r)
            key=(str(d.get('unit_title') or '').strip(),str(d.get('topic') or '').strip())
            if key not in seen:
                seen.add(key); out.append({'key':key,'unit_title':key[0],'topic':key[1]})
        return out
    finally: con.close()

def _beta50_rpt_lessons(year_label, subject, unit_key):
    con=_db()
    try:
        rows=con.execute("""SELECT id,sequence_no,unit_code,unit_title,topic,subtopic,theme,skill_focus
                            FROM rpt_entries
                            WHERE year_label=? AND subject=? AND verified=1
                              AND content_verified=1 AND sequence_verified=1
                              AND COALESCE(unit_title,'')=? AND COALESCE(topic,'')=?
                            ORDER BY sequence_no,id""",(year_label,subject,unit_key[0],unit_key[1])).fetchall()
        return [dict(r) for r in rows]
    finally: con.close()

def show_beta50_units(cid, page=0):
    st=state.setdefault(cid,{})
    units=_beta50_rpt_units(st.get('year',''),st.get('subject',''))
    if not units: return show_topics(cid,0)
    st['beta50_units']=units
    per=8; start=page*per; end=min(start+per,len(units)); kb=[]
    for i in range(start,end):
        u=units[i]; label=u.get('topic') or u.get('unit_title') or f'Unit {i+1}'
        kb.append([{'text':'📚 '+str(label)[:55],'callback_data':f'b50unit_{i}'}])
    nav=[]
    if page>0: nav.append({'text':'⬅️ Sebelum','callback_data':f'b50up_{page-1}'})
    if end<len(units): nav.append({'text':'Seterusnya ➡️','callback_data':f'b50up_{page+1}'})
    if nav: kb.append(nav)
    kb.append([{'text':'⬅️ Pilih Subjek','callback_data':'back_subjects'},{'text':'🏠 Menu Utama','callback_data':'home'}])
    send(cid,f'📚 <b>{st.get("subject","")} — {st.get("year","")}</b>\n\nPilih <b>Unit/Tajuk</b>. Selepas itu pilih Lesson; SK/SP akan dipadankan automatik.',kb)

def show_beta50_lessons(cid, unit_index, page=0):
    st=state.setdefault(cid,{})
    units=st.get('beta50_units') or _beta50_rpt_units(st.get('year',''),st.get('subject',''))
    if unit_index<0 or unit_index>=len(units): return show_beta50_units(cid,0)
    st['beta50_unit_index']=unit_index; u=units[unit_index]
    lessons=_beta50_rpt_lessons(st.get('year',''),st.get('subject',''),tuple(u['key']))
    st['beta50_lessons']=lessons
    per=10; start=page*per; end=min(start+per,len(lessons)); kb=[]
    for i in range(start,end):
        r=lessons[i]; code=str(r.get('unit_code') or f'Lesson {r.get("sequence_no",i+1)}').strip()
        focus=str(r.get('skill_focus') or '').strip(); label=code+(f' • {focus}' if focus else '')
        kb.append([{'text':'📖 '+label[:58],'callback_data':f'b50lesson_{i}'}])
    nav=[]
    if page>0: nav.append({'text':'⬅️ Sebelum','callback_data':f'b50lp_{unit_index}_{page-1}'})
    if end<len(lessons): nav.append({'text':'Seterusnya ➡️','callback_data':f'b50lp_{unit_index}_{page+1}'})
    if nav: kb.append(nav)
    kb.append([{'text':'⬅️ Unit/Tajuk','callback_data':'b50units'},{'text':'🏠 Menu Utama','callback_data':'home'}])
    send(cid,f'📖 <b>{u.get("topic") or u.get("unit_title")}</b>\n\nPilih <b>Lesson</b>. SK/SP tidak perlu dipilih kali kedua.',kb)

def _beta50_select_lesson(cid, lesson_index):
    st=state.setdefault(cid,{})
    lessons=st.get('beta50_lessons') or []
    if lesson_index<0 or lesson_index>=len(lessons): return show_beta50_units(cid,0)
    r=lessons[lesson_index]; rid=int(r['id']); con=_db()
    try:
        std=[dict(x) for x in con.execute("""SELECT standard_type,standard_code,standard_text,role,sequence_no
                                             FROM rpt_entry_standards
                                             WHERE rpt_entry_id=? AND verified=1
                                             ORDER BY CASE standard_type WHEN 'SK' THEN 0 ELSE 1 END,sequence_no,id""",(rid,)).fetchall()]
    finally: con.close()
    st['rpt_entry_id']=rid; st['textbook_lesson_no']=str(r.get('unit_code') or r.get('sequence_no') or '')
    st['topic']=str(r.get('topic') or r.get('unit_title') or '').strip()
    st['subtopic']=str(r.get('subtopic') or r.get('skill_focus') or '').strip()
    st['theme']=str(r.get('theme') or '').strip(); st['textbook_page_focus']=str(r.get('skill_focus') or '').strip()
    sk=[x for x in std if x.get('standard_type')=='SK']; sp=[x for x in std if x.get('standard_type')=='SP']
    if not sk or not sp:
        return send(cid,'ℹ️ <b>Lesson ini tidak mempunyai fixed SK/SP dalam SOW yang disahkan.</b>\n\nCikguLaju tidak akan mereka standard. Pilih Lesson lain untuk Beta 50%.',[[{'text':'⬅️ Pilih Lesson Lain','callback_data':f'b50unit_{st.get("beta50_unit_index",0)}'},{'text':'🏠 Menu Utama','callback_data':'home'}]])
    opts=[]; parent=sk[0]
    for x in sp:
        opts.append({'sk_code':parent['standard_code'],'sk_text':parent['standard_text'],'sp_code':x['standard_code'],'sp_text':x['standard_text']})
    st['selected_sp_codes']=[x['sp_code'] for x in opts]; st['multi_sp_options']=opts
    _commit_multi_sp(st,opts)
    send(cid,f'✅ <b>{html.escape(st["textbook_lesson_no"])}</b> dipilih.\nSK/SP telah dipadankan automatik daripada RPT/SOW verified.',None)
    st['beta50_verified_lesson']=True; st['beta50_curriculum_locked']=True
    return after_curriculum_selected(cid)
'''

if MARK not in s:
    anchor="def show_topics(cid, page=0):"
    if anchor not in s: raise SystemExit("Beta50 patch anchor show_topics missing")
    s=s.replace(anchor,block+"\n"+anchor,1)

old="""        if s0.get('task')=='bbm':
            s0['assessment_mode']='formative'
            return show_topics(cid,0)"""
new="""        if s0.get('task')=='bbm':
            s0['assessment_mode']='formative'
            return show_beta50_units(cid,0) if _beta50_rpt_units(s0.get('year',''),s0.get('subject','')) else show_topics(cid,0)"""
if old in s: s=s.replace(old,new,1)

handler="""    elif d == 'b50units':
        return show_beta50_units(cid,0)
    elif d.startswith('b50up_'):
        try: return show_beta50_units(cid,int(d.split('_',1)[1]))
        except Exception: return show_beta50_units(cid,0)
    elif d.startswith('b50unit_'):
        try: return show_beta50_lessons(cid,int(d.split('_',1)[1]),0)
        except Exception: return show_beta50_units(cid,0)
    elif d.startswith('b50lp_'):
        try:
            _,ui,pg=d.split('_'); return show_beta50_lessons(cid,int(ui),int(pg))
        except Exception: return show_beta50_units(cid,0)
    elif d.startswith('b50lesson_'):
        try: return _beta50_select_lesson(cid,int(d.split('_',1)[1]))
        except Exception as e:
            print('Beta50 lesson select error:',repr(e),flush=True); return show_beta50_units(cid,0)
"""
if "elif d == 'b50units':" not in s:
    anchor="    elif d == 'fast_use_rpt':"
    if anchor not in s: raise SystemExit("Beta50 callback anchor missing")
    s=s.replace(anchor,handler+anchor,1)

P.write_text(s,encoding="utf-8")
print("BETA50 patch applied", P.stat().st_size)


# ENGLISH_Y1Y2_BOT_READY_V1_APPLY
# Apply the English Year 1-2 BOT_READY runtime patch after the existing Beta50 patch.
import subprocess, sys
_eng_patch=Path(__file__).with_name("tools").joinpath("patch_english_y1y2_bot_ready_v1.py")
if _eng_patch.exists():
    subprocess.check_call([sys.executable, str(_eng_patch), str(P)])
else:
    print("English Y1Y2 BOT_READY patch helper missing:", _eng_patch)
