"""Music 2027 native Telegram navigation candidate; strictly staging only.

Never installed by the LIVE WSGI. Install requires both the emergency feature
flag and a separate explicit cross-platform parity approval. Do not claim
FINAL READY; preserve original Telegram accounts, class/date, credits and DB.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import re

from .native_layout_preview_staging import build_staging_preview
from .external_audio_links_staging import audio_link_action

ROOT=Path(__file__).resolve().parent
SUBJECT="Pendidikan Muzik"
SESSION_KEY="_muzik2027_verified_pdp"
FLAG="CIKGULAJU_MUZIK_2027_PROVISIONAL_ENABLED"
PARITY_FLAG="CIKGULAJU_MUZIK_2027_WEB_TELEGRAM_PARITY_APPROVED"


def _year(value):
    match=re.fullmatch(r"(?:Tahun\s*)?([2-6])(?:\s*\(SK\))?",str(value or "").strip(),re.I)
    return int(match.group(1)) if match else None


def source_paths(year,pdp):
    if type(year) is not int or type(pdp) is not int or not 2<=year<=6 or not 1<=pdp<=35:
        return ()
    return (
        f"year{year}/rph_pdp_{pdp:02d}.md",
        f"year{year}/pdp_manifest.json",
        f"year{year}/RPT_MUZIK_TAHUN_{year}_2027_DRAF.csv",
        "SUCCESS_CRITERIA_DRAFT_20261106.json",
        "DSKP_SP_CODE_PRESENCE_175_20261106.json",
    )


def source_digest(year,pdp,*,root=ROOT):
    """Byte-identical source identity, with explicit path / size guards."""
    sources=source_paths(year,pdp)
    if not sources:
        return None
    base=Path(root).resolve()
    result=sha256()
    for relative in sources:
        path=base/relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(base):
            return None
        try:
            if not 0<path.stat().st_size<=2_500_000:
                return None
            raw=path.read_bytes()
        except OSError:
            return None
        result.update(relative.encode("utf-8"))
        result.update(b"\0")
        result.update(raw)
        result.update(b"\0")
    return result.hexdigest()


def load(year,pdp,*,root=ROOT):
    """Read exactly one source-backed PdP, never infer a lesson from RPT week."""
    digest=source_digest(year,pdp,root=root)
    if digest is None:
        return None
    try:
        preview=build_staging_preview(root,year,pdp)
        manifest=json.loads((Path(root)/f"year{year}"/"pdp_manifest.json").read_text(encoding="utf-8"))
        row=manifest["pdps"][pdp-1]
        if (row["pdp_id"]!=preview["source_pdp_id"] or row["pdp"]!=pdp
                or manifest.get("academic_year")!=2027
                or "DRAF" not in manifest.get("status","")
                or any(manifest.get(key) is not False
                       for key in ("textbook_verified","audio_verified","rph_word_pdf_verified"))
                or preview.get("approved_for_live") is not False):
            return None
        header={x["label"]:x["value"] for x in preview["layout"]["header"]}
        if header["Tajuk"]!=row["unit"] or not header.get("Standard Pembelajaran"):
            return None
        return {
            "year":year,"pdp":pdp,"subject":SUBJECT,"title":row["unit"],
            "digest":digest,"sk":header["Standard Kandungan"].split("; "),
            "sp":row["sp"],"preview":preview,
            "unofficial":row.get("pdp_kind")=="CADANGAN_PENGUKUHAN_BUKAN_PROJEK_RASMI",
        }
    except (ValueError,TypeError,KeyError,OSError,IndexError):
        return None


def _selection(state,*,root=ROOT):
    if not isinstance(state,dict) or state.get("subject")!=SUBJECT:
        return None
    token=state.get(SESSION_KEY)
    year=_year(state.get("year") or state.get("year_label"))
    if not isinstance(token,dict) or year is None:
        return None
    pdp=token.get("pdp")
    if (type(pdp) is not int or token.get("year")!=year or token.get("subject")!=SUBJECT
            or str(state.get("lesson_no") or "")!=str(pdp)):
        return None
    selected=load(year,pdp,root=root)
    if (selected is None or selected["digest"]!=token.get("digest")
            or state.get("sp_code") not in selected["sp"]):
        return None
    return selected


def adapt_rows(state,rows,*,root=ROOT):
    """Populate the original native Telegram Word/PDF row layout only."""
    if not isinstance(rows,dict):
        raise ValueError("Invalid Telegram RPH rows")
    if not isinstance(state,dict) or state.get("subject")!=SUBJECT or SESSION_KEY not in state:
        return rows
    src=_selection(state,root=root)
    if src is None:
        # A stale callback must never emit a generic Music RPH.
        raise ValueError("Stale or unverified Music source selection")
    preview=src["preview"]
    header={x["label"]:x["value"] for x in preview["layout"]["header"]}
    result=dict(rows)
    result.update({
        "MATA PELAJARAN":SUBJECT,
        "TAHUN/TINGKATAN":f"Tahun {src['year']}",
        "TAJUK":src["title"],
        "STANDARD KANDUNGAN":header["Standard Kandungan"],
        "STANDARD PEMBELAJARAN":header["Standard Pembelajaran"],
        "OBJEKTIF PEMBELAJARAN":header["OBJEKTIF PEMBELAJARAN"],
        "KRITERIA KEJAYAAN":header["KRITERIA KEJAYAAN"],
        "SET INDUKSI":preview["phase_text"]["induction"],
        "AKTIVITI UTAMA":preview["layout"]["phases"][1]["activity"],
        "PENTAKSIRAN":preview["phase_text"]["assessment"],
        "PENUTUP":preview["phase_text"]["closure"],
        "BAHAN BANTU MENGAJAR":preview["phase_text"]["materials"],
    })
    return result


def install(ns,*,root=ROOT):
    """Opt-in candidate only; never edit the master DB or debit RPH credits."""
    if os.environ.get(FLAG)!="1" or os.environ.get(PARITY_FLAG)!="1":
        return False
    if not isinstance(ns,dict) or not isinstance(ns.get("state"),dict):
        return False
    if ns.get("MUZIK_2027_NATIVE_CANDIDATE_ACTIVE"):
        return True
    required=("callback","subjects","send","_rph_rows","_lesson_to_class_v2439")
    if any(not callable(ns.get(key)) for key in required):
        return False
    root=Path(root).resolve()
    if any(load(y,p,root=root) is None for y in range(2,7) for p in range(1,36)):
        return False
    old_cb,old_subjects,old_rows=ns["callback"],ns["subjects"],ns["_rph_rows"]
    send,session=ns["send"],ns["state"]

    def menu(cid,page=0):
        st=session.setdefault(cid,{})
        year=_year(st.get("year"))
        if year is None or st.get("subject")!=SUBJECT:
            return old_cb(cid,"choose_grade")
        page=max(0,min(4,page))
        first=page*7+1
        kb=[]
        for pdp in range(first,min(first+7,36)):
            row=load(year,pdp,root=root)
            if row is None:
                return send(cid,"Sumber Muzik tidak sepadan. Pilih semula subjek.")
            buttons = [{"text":(f"PdP {pdp:02d} — {row['title']}")[:52],
                        "callback_data":f"muzik27pick|{year}|{pdp:02d}"}]
            if audio_link_action(year,pdp,root=root)["available"]:
                buttons.append({"text":"🔊","callback_data":f"muzik27audio|{year}|{pdp:02d}|0"})
            kb.append(buttons)
        nav=[]
        if page>0:
            nav.append({"text":"⬅️","callback_data":f"muzik27page|{year}|{page-1}"})
        if first+7<=35:
            nav.append({"text":"➡️","callback_data":f"muzik27page|{year}|{page+1}"})
        if nav:
            kb.append(nav)
        kb.append([{"text":"⬅️ Tukar tahun/subjek","callback_data":"choose_grade"}])
        return send(cid,f"🎵 <b>Pendidikan Muzik Tahun {year}</b>\n\n"
                        "Pilih PdP, kemudian kelas, tarikh dan bahan RPH Word/PDF.",kb)

    def subjects(cid,label):
        year=_year(label)
        catalog=ns.get("SUBJECTS_BY_GRADE")
        if year is None or not isinstance(catalog,dict):
            return old_subjects(cid,label)
        session.setdefault(cid,{})["year"]=label
        seen=set();buttons=[]
        labels=ns.get("SUBJECT_LABEL") or {}
        for name in catalog.get(label,()) or ():
            if name not in seen:
                seen.add(name)
                buttons.append({"text":labels.get(name,name),"callback_data":"sub_"+name})
        if SUBJECT not in seen:
            seen.add(SUBJECT)
            buttons.append({"text":"🎵 Pendidikan Muzik","callback_data":"sub_"+SUBJECT})
        for name,years in (ns.get("_CIKGULAJU_DEV_SUBJECTS_V2617") or {}).items():
            if name!=SUBJECT and name not in seen and year in years:
                buttons.append({"text":"🚧 "+name+" (Dalam Pembangunan)",
                                "callback_data":"devsub2617_"+name})
        kb=[buttons[i:i+2] for i in range(0,len(buttons),2)]
        kb.extend([[{"text":"⬅️ Pilih Tahun/Tingkatan","callback_data":"choose_grade"}],
                   [{"text":"🏠 Menu Utama","callback_data":"home"}]])
        return send(cid,f"📘 <b>{label}</b>\n\nPilih subjek.",kb)

    def audio_menu(cid,year,pdp,page=0):
        """Show source-view URLs, never a CikguLaju download endpoint."""
        st=session.setdefault(cid,{})
        if _year(st.get("year"))!=year or st.get("subject")!=SUBJECT:
            return send(cid,"Pilihan audio tidak sepadan dengan Tahun/Subjek. Pilih semula.")
        if load(year,pdp,root=root) is None:
            return send(cid,"Sumber PdP Muzik belum dapat disahkan.")
        audio=audio_link_action(year,pdp,root=root)
        if not audio["available"]:
            return send(cid,"Audio untuk PdP ini belum mempunyai pautan sumber yang jelas.")
        links=audio["links"]
        if type(page) is not int or not 0<=page<=(len(links)-1)//6:
            return send(cid,"Halaman audio tidak sah.")
        start=page*6
        kb=[[{"text":("🔊 Audio %03d • %s" % (x["track"],x["title"]))[:63],
              "url":x["url"]}] for x in links[start:start+6]]
        nav=[]
        if page:
            nav.append({"text":"⬅️ Audio sebelumnya",
                        "callback_data":f"muzik27audio|{year}|{pdp:02d}|{page-1}"})
        if start+6<len(links):
            nav.append({"text":"➡️ Audio seterusnya",
                        "callback_data":f"muzik27audio|{year}|{pdp:02d}|{page+1}"})
        if nav:
            kb.append(nav)
        kb.append([{"text":"⬅️ Senarai PdP Muzik",
                    "callback_data":f"muzik27page|{year}|{(pdp-1)//7}"}])
        return send(cid,
            "🎵 <b>Audio sumber • Tahun %d • PdP %02d</b>\n\n"
            "Pautan Google Drive asal sahaja. Padanan nombor belum membuktikan "
            "rakaman tepat; akses serta kebenaran edaran belum disahkan. "
            "Gunakan fungsi pemilik Google Drive jika muat turun dibenarkan." % (year,pdp),kb)

    def callback(cid,data):
        value=str(data or "")
        st=session.setdefault(cid,{})
        if value in ("sub_Pendidikan Muzik","devsub2617_Pendidikan Muzik"):
            if _year(st.get("year")) is None:
                return old_cb(cid,data)
            st["subject"]=SUBJECT
            st.pop(SESSION_KEY,None)
            return menu(cid)
        if value.startswith("muzik27audio|"):
            parts=value.split("|")
            if (len(parts)!=4 or not all(x.isascii() and x.isdecimal() for x in parts[1:])
                    or len(parts[2])!=2):
                return send(cid,"Pilihan audio Muzik tidak sah.")
            return audio_menu(cid,int(parts[1]),int(parts[2]),int(parts[3]))
        if value.startswith(("muzik27page|","muzik27pick|")):
            parts=value.split("|")
            if (len(parts)!=3 or not all(part.isascii() and part.isdecimal()
                                         for part in parts[1:])):
                return send(cid,"Pilihan Muzik tidak sah.")
            year=int(parts[1])
            if _year(st.get("year"))!=year or st.get("subject")!=SUBJECT:
                return send(cid,"Pilihan Muzik telah berubah. Pilih semula subjek.")
            if value.startswith("muzik27page|"):
                return menu(cid,int(parts[2]))
            if len(parts[2])!=2:
                return menu(cid)
            pdp=int(parts[2])
            selected=load(year,pdp,root=root)
            if selected is None:
                return menu(cid)
            for field in ("selected_sk","sk_code","selected_sp","sp_code",
                          "selected_sk_codes","selected_sp_codes",
                          "grouped_sk_codes","grouped_sp_codes","lesson","lesson_no",
                          "pdp_no","topic","subtopic","unit","unit_title",
                          "quick_content_v2391","textbook_lesson_no"):
                st.pop(field,None)
            st.update({
                "subject":SUBJECT,"task":"quick_material","quick_material_flow":True,
                "assessment_mode":"formative","rph_mode":"fast_rpt",
                "lesson":str(pdp),"lesson_no":str(pdp),"pdp_no":pdp,
                "topic":selected["title"],"unit":selected["title"],
                "unit_title":selected["title"],
                "sk_code":selected["sk"][0],"sp_code":selected["sp"][0],
                "selected_sk":selected["sk"][0],"selected_sp":selected["sp"][0],
                "selected_sk_codes":list(selected["sk"]),
                "selected_sp_codes":list(selected["sp"]),
                "grouped_sk_codes":list(selected["sk"]),
                "grouped_sp_codes":list(selected["sp"]),
                "quick_content_v2391":selected["title"],
                SESSION_KEY:{"year":year,"pdp":pdp,"subject":SUBJECT,
                             "digest":selected["digest"]},
            })
            return ns["_lesson_to_class_v2439"](cid)
        return old_cb(cid,data)

    def rows(state,*args,**kwargs):
        original=old_rows(state,*args,**kwargs)
        return adapt_rows(state,original,root=root)

    ns["callback"]=callback
    ns["subjects"]=subjects
    ns["_rph_rows"]=rows
    ns["MUZIK_2027_NATIVE_CANDIDATE_ACTIVE"]=True
    return True
