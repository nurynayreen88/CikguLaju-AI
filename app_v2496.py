import os, re, html
os.environ.setdefault("CIKGULAJU_DB_PATH", os.path.join(os.path.dirname(__file__), "CikguLaju_Curriculum_Master_v24_95_CORE.db"))
import app as base

app = base.app
base.APP_VERSION = "v24.96-BM-VERIFIED-PDP-FLOW"

def _rows(year):
    con=base._db()
    try:
        rs=con.execute("""SELECT * FROM verified_pdp_sequence
          WHERE year_label=? AND subject='Bahasa Melayu'
          AND COALESCE(verification_status,'') NOT IN ('REJECT_NON_SK','SOURCE_NONCORE')
          ORDER BY CASE WHEN week_no IS NULL THEN 999 ELSE week_no END,id""",(year,)).fetchall()
        return [dict(r) for r in rs]
    finally:
        con.close()

def _uniq(vals):
    out=[]; seen=set()
    for x in vals:
        v=str(x or "").strip()
        if v and v.casefold() not in seen:
            seen.add(v.casefold()); out.append(v)
    return out

def theme_menu(cid,page=0):
    ss=base.state.setdefault(cid,{})
    rows=_rows(ss.get("year","")); themes=_uniq(r.get("theme") for r in rows)
    ss["_bm96_rows"]=rows; ss["_bm96_themes"]=themes
    if not themes:
        return base.send(cid,"🚧 <b>Urutan PdP Bahasa Melayu verified belum tersedia untuk tahun ini.</b>",[[{"text":"🏠 Menu Utama","callback_data":"home"}]])
    per=10; page=max(0,int(page or 0)); a=page*per; b=min(a+per,len(themes)); kb=[]
    for i in range(a,b):
        kb.append([{"text":("🟦 "+themes[i])[:60],"callback_data":f"bm96_theme_{i}"}])
    nav=[]
    if a: nav.append({"text":"⬅️ Sebelum","callback_data":f"bm96_tp_{page-1}"})
    if b<len(themes): nav.append({"text":"Seterusnya ➡️","callback_data":f"bm96_tp_{page+1}"})
    if nav: kb.append(nav)
    kb.append([{"text":"⬅️ Tukar Subjek","callback_data":"choose_grade"},{"text":"🏠 Menu Utama","callback_data":"home"}])
    return base.send(cid,f"🇲🇾 <b>Bahasa Melayu • {html.escape(str(ss.get('year') or ''))}</b>\n\nPilih <b>Tema</b>. Tema → Unit → Tajuk PdP → SK/SP automatik.",kb)

def unit_menu(cid,ti):
    ss=base.state.setdefault(cid,{})
    themes=ss.get("_bm96_themes") or []
    if ti<0 or ti>=len(themes): return theme_menu(cid)
    theme=themes[ti]; units=[]; seen=set()
    for r in ss.get("_bm96_rows") or []:
        if str(r.get("theme") or "").strip()!=theme: continue
        key=(str(r.get("unit_code") or "").strip(),str(r.get("unit_title") or "").strip())
        if key not in seen: seen.add(key); units.append(key)
    ss["_bm96_theme"]=theme; ss["_bm96_units"]=units
    kb=[]
    for i,(code,title) in enumerate(units):
        label=(f"Unit {code} • " if code else "")+title
        kb.append([{"text":("📘 "+label)[:60],"callback_data":f"bm96_unit_{i}"}])
    kb.append([{"text":"⬅️ Tukar Tema","callback_data":"bm96_tp_0"}])
    return base.send(cid,f"🟦 <b>{html.escape(theme)}</b>\n\nPilih <b>Unit</b>.",kb)

def pdp_menu(cid,ui):
    ss=base.state.setdefault(cid,{})
    units=ss.get("_bm96_units") or []
    if ui<0 or ui>=len(units): return theme_menu(cid)
    code,title=units[ui]; theme=ss.get("_bm96_theme","")
    rows=[r for r in ss.get("_bm96_rows") or [] if str(r.get("theme") or "").strip()==theme and str(r.get("unit_code") or "").strip()==code and str(r.get("unit_title") or "").strip()==title]
    titles=_uniq(r.get("pdp_title") for r in rows)
    ss["_bm96_unit"]=(code,title); ss["_bm96_pdp_rows"]=rows; ss["_bm96_pdp_titles"]=titles
    kb=[[{"text":("▶️ "+p)[:60],"callback_data":f"bm96_pdp_{i}"}] for i,p in enumerate(titles)]
    kb.append([{"text":"⬅️ Tukar Tema","callback_data":"bm96_tp_0"}])
    label=(f"Unit {code} • " if code else "")+title
    return base.send(cid,f"📘 <b>{html.escape(label)}</b>\n\nPilih <b>Tajuk PdP</b>. SK/SP automatik; Kemahiran hanya metadata.",kb)

def commit_pdp(cid,pi):
    ss=base.state.setdefault(cid,{})
    titles=ss.get("_bm96_pdp_titles") or []
    if pi<0 or pi>=len(titles): return theme_menu(cid)
    pdp=titles[pi]; rows=[r for r in ss.get("_bm96_pdp_rows") or [] if str(r.get("pdp_title") or "").strip()==pdp]
    if not rows: return theme_menu(cid)
    r0=rows[0]; code,title=ss.get("_bm96_unit") or ("","")
    ss.update({"task":"quick_material","quick_material_flow":True,"rph_mode":"fast_rpt","assessment_mode":"formative",
               "topic":title,"subtopic":pdp,"pdp_title":pdp,"rpt_theme":str(r0.get("theme") or ""),
               "rpt_unit_title":title,"rpt_topic":pdp,"skill_metadata":str(r0.get("skill_metadata") or ""),
               "textbook_ref":str(r0.get("textbook_ref") or ""),"activitybook_ref":str(r0.get("activitybook_ref") or "")})
    mapped=[]
    for r in rows:
        sk=str(r.get("sk_code") or "").strip(); sp=str(r.get("sp_code") or "").strip()
        if sp: mapped.append({"sk_code":sk,"sk_text":"","sp_code":sp,"sp_text":""})
    if not mapped:
        return base.send(cid,"🚧 <b>SK/SP verified untuk PdP ini belum lengkap.</b>",[[{"text":"🏠 Menu Utama","callback_data":"home"}]])
    base._commit_multi_sp(ss,mapped[:8])
    return base._temporary_auto_pack_v2386(cid)

_old_callback=base.callback
def callback(cid,d):
    ss=base.state.setdefault(cid,{})
    ds=str(d or "")
    if ds.startswith("sub_") and ds[4:]=="Bahasa Melayu" and base._is_quick_pdp_v2428(ss):
        ss["subject"]="Bahasa Melayu"; ss["assessment_mode"]="formative"; ss["quick_material_flow"]=True
        for k in ("topic","subtopic","selected_sk","selected_sp","_bm96_rows","_bm96_themes","_bm96_units","_bm96_pdp_rows","_bm96_pdp_titles"):
            ss.pop(k,None)
        return theme_menu(cid)
    if ds.startswith("bm96_tp_"):
        try: p=int(ds.rsplit("_",1)[1])
        except: p=0
        return theme_menu(cid,p)
    if ds.startswith("bm96_theme_"):
        try: i=int(ds.rsplit("_",1)[1])
        except: i=-1
        return unit_menu(cid,i)
    if ds.startswith("bm96_unit_"):
        try: i=int(ds.rsplit("_",1)[1])
        except: i=-1
        return pdp_menu(cid,i)
    if ds.startswith("bm96_pdp_"):
        try: i=int(ds.rsplit("_",1)[1])
        except: i=-1
        return commit_pdp(cid,i)
    return _old_callback(cid,d)

base.callback=callback
