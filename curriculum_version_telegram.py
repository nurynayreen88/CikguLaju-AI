"""Show curriculum versions and DLP previews inside Telegram's RPH selectors."""
from html import escape

from curriculum_version_selector import KP2027, LEGACY, resolve_curriculum


DLP_PREVIEWS = {
    "cv_dlp_science": (
        "Science (DLP)",
        "Unit 1 Scientific Skills · Observe",
        "CS 1.1 · LS 1.1.1",
        "Pupils record three observations using sight, touch and hearing, then identify the sense used for each observation.",
        "Science Year 2 Textbook pp. 2–4 · Activity Book pp. 1–2",
    ),
    "cv_dlp_math": (
        "Mathematics (DLP)",
        "Unit 1 Numbers up to 1,000 · Recognise Numbers",
        "CS 1.1 · LS 1.1.1(i)–(iii)",
        "Pupils read two numerals aloud and match at least four out of five numerals to their word forms.",
        "Mathematics Year 2 Textbook Part 1 pp. 2–4 · Activity Book pp. 1–2",
    ),
}


def _rph_flow(st):
    return st.get("task") in ("quick_material", "rph")


def install(namespace):
    previous_callback=namespace["callback"]
    previous_subjects=namespace["subjects"]
    previous_year=namespace["year"]
    state=namespace["state"]
    send=namespace["send"]
    subjects_by_grade=namespace["SUBJECTS_BY_GRADE"]
    subject_label=namespace["SUBJECT_LABEL"]
    preview_subject_years=namespace.get("_CIKGULAJU_DEV_SUBJECTS_V2617", {})

    def year(cid, level):
        if str(level).lower() != "primary" or not _rph_flow(state.get(cid, {})):
            return previous_year(cid, level)
        keyboard = [
            [{"text":"Tahun 1 (KP Baharu)", "callback_data":"cv_year1_kp"},
             {"text":"Tahun 1 (KSSR)", "callback_data":"year_1"}],
            *[[{"text":f"Tahun {n}", "callback_data":f"year_{n}"} for n in row]
              for row in ((2, 3), (4, 5), (6,))],
            [{"text":"⬅️ Pilih Peringkat Sekolah", "callback_data":"choose_grade"}],
            [{"text":"🏠 Menu Utama", "callback_data":"home"}],
        ]
        return send(cid, "🏫 <b>Sekolah Rendah</b>\n\nPilih Tahun:", keyboard)

    def choose_year_one_preview(cid):
        st = state.get(cid, {})
        # Discard any earlier Lesson/standard/pending generation selection.
        state[cid] = {key: st[key] for key in ("task", "quick_material_flow", "rph_mode", "_cid") if key in st}
        state[cid].update(year="Tahun 1", curriculum_version=KP2027)
        return subjects(cid, "Tahun 1")

    def choose(cid,label):
        st=state.setdefault(cid,{})
        st["year"]=label
        st.pop("subject",None)
        st.pop("topic",None)
        if label != "Tingkatan 1" and (label != "Tahun 1" or _rph_flow(st)):
            st["curriculum_version"]=LEGACY
            return subjects(cid,label)
        previous=st.get("curriculum_version",LEGACY)
        return send(cid,"📚 <b>"+label+"</b>\n\nPilih kurikulum:",[
            [{"text":("✅ " if previous==LEGACY else "")+"KSSR/KSSM Sedia Ada","callback_data":"cv_existing"}],
            [{"text":("✅ " if previous==KP2027 else "")+"Kurikulum Persekolahan 2027 (KP2027)","callback_data":"cv_kp2027"}],
            [{"text":"⬅️ Tahun/Tingkatan","callback_data":"choose_grade"}]])
    def subjects(cid,label):
        st=state.setdefault(cid,{})
        result=resolve_curriculum(st.get("curriculum_version"),label,st.get("subject"))
        if st.get("curriculum_version")==KP2027 and label in ("Tahun 1", "Tingkatan 1"):
            # Display candidate subjects only; never route into legacy SK/SP.
            candidates=list(subjects_by_grade.get(label,()) or ())
            if label=="Tahun 1":
                # Temporary KP2027 menu-only hide; preserve legacy and stored data.
                hidden={"BC","BT","Bahasa Cina","Bahasa Tamil"}
                candidates=[sub for sub in candidates
                            if sub not in hidden and subject_label.get(sub,sub) not in hidden]
            kb=[[{"text":subject_label.get(sub,sub)+" — Akan Datang",
                  "callback_data":"cv_build_"+str(i)}]
                for i,sub in enumerate(candidates)]
            st["_kp2027_subject_candidates"]=candidates
            kb.extend([[{"text":"📖 Pratonton Kerangka Rasmi KP2027","callback_data":"cv_preview"}],
                       [{"text":"⬅️ Pilih Tahun","callback_data":"cv_choose"}],
                       [{"text":"🏠 Menu Utama","callback_data":"home"}]])
            return send(cid,"📚 <b>"+label+" (KP Baharu)</b>\n\n"
                        "Bahan Kurikulum Persekolahan 2027 sedang disemak. Janaan RPH berstatus Akan Datang.",kb)
        if not result["enabled"]:
            return send(cid,"⏳ KP2027 belum tersedia.",[[{"text":"⬅️ Tukar Kurikulum","callback_data":"cv_choose"}]])
        if label == "Tahun 2" and _rph_flow(st):
            st["year"] = label
            existing = list(subjects_by_grade.get(label, ()))
            buttons = [{"text":subject_label.get(sub,sub), "callback_data":"sub_"+sub} for sub in existing]
            buttons.extend(
                {"text":name+" — Akan Datang", "callback_data":"devsub2617_"+name}
                for name, years in preview_subject_years.items() if 2 in years and name not in existing
            )
            keyboard = [buttons[i:i+2] for i in range(0,len(buttons),2)]
            keyboard.extend([{"text":preview[0]+" — Akan Datang", "callback_data":key}]
                            for key, preview in DLP_PREVIEWS.items())
            keyboard.extend([[{"text":"⬅️ Pilih Tahun", "callback_data":"level_primary"}],
                             [{"text":"🏠 Menu Utama", "callback_data":"home"}]])
            return send(cid,"📘 <b>Tahun 2</b>\n\nPilih subjek.",keyboard)
        return previous_subjects(cid,label)

    def callback(cid,d):
        st=state.setdefault(cid,{})
        if d == "cv_year1_kp":
            return choose_year_one_preview(cid) if _rph_flow(st) else year(cid, "primary")
        if d in DLP_PREVIEWS:
            if not (_rph_flow(st) and st.get("year") == "Tahun 2" and st.get("curriculum_version") == LEGACY):
                return year(cid, "primary")
            name, topic, standards, objective, books = DLP_PREVIEWS[d]
            return send(cid, f"<b>{name} · Year 2</b>\n{topic}\n{standards}\n\n{objective}\n{books}\n\n"
                        "Pratonton. Janaan RPH dan muat turun berstatus Akan Datang.",
                        [[{"text":"⬅️ Pilih Subjek", "callback_data":"back_subjects"}],
                         [{"text":"🏠 Menu Utama", "callback_data":"home"}]])
        if d.startswith("year_"):
            return choose(cid,"Tahun "+d[5:])
        if d.startswith("form_"):
            return choose(cid,"Tingkatan "+d[5:])
        if d=="cv_choose":
            label = st.get("year","Tahun 1")
            if label=="Tingkatan 1" or not _rph_flow(st):
                return choose(cid,label)
            return year(cid,"primary")
        if d in ("cv_existing","cv_kp2027"):
            if d=="cv_kp2027" and st.get("year","Tahun 1")=="Tahun 1":
                return choose_year_one_preview(cid)
            st["curriculum_version"]=LEGACY if d=="cv_existing" else KP2027
            return subjects(cid,st.get("year","Tahun 1"))
        if d.startswith("cv_build_"):
            if st.get("curriculum_version") != KP2027:
                return year(cid, "primary")
            try:
                idx=int(d[len("cv_build_"):])
                sub=st.get("_kp2027_subject_candidates",[])[idx]
                if idx<0: raise IndexError()
            except (ValueError,IndexError):
                return subjects(cid,st.get("year","Tahun 1"))
            return send(cid,"<b>"+escape(subject_label.get(sub,sub))+" — KP Baharu</b>\n"
                        "Akan Datang. Dokumen rasmi dan pemetaan SK/SP sedang disemak; "
                        "penjanaan RPH belum dibuka.",[
                        [{"text":"⬅️ Senarai Subjek KP Baharu","callback_data":"cv_subjects"}],
                        [{"text":"🏠 Menu Utama","callback_data":"home"}]])
        if d=="cv_preview":
            label=st.get("year","Tahun 1")
            return send(cid,
                "📖 <b>"+escape(label)+" (KP Baharu)</b>\n\n"
                "<b>Apa yang baharu?</b>\n"
                "• Pelaksanaan berperingkat bermula pada 2027 untuk Tahun 1 dan Tingkatan 1.\n"
                "• Kerangka memberi perhatian kepada pembentukan karakter, "
                "perkembangan kompetensi dan pembelajaran bermakna.\n"
                "• Kandungan khusus setiap subjek akan dimasukkan selepas dokumen "
                "kurikulum rasminya disahkan.\n\n"
                "🚧 <b>Status CikguLaju:</b> Pratonton tersedia; SK/SP, pemetaan "
                "PdP dan janaan RPH KP2027 berstatus Akan Datang.\n"
                "<i>Ringkasan berdasarkan kerangka KPM, bukan DSKP mata pelajaran.</i>",[
                [{"text":"📚 Lihat Subjek KP2027","callback_data":"cv_subjects"}],
                [{"text":"🏠 Menu Utama","callback_data":"home"}]])
        if d=="cv_subjects":
            return subjects(cid,st.get("year","Tahun 1"))
        if st.get("curriculum_version")==KP2027 and (
                d.startswith(("sub_", "topic_", "st3|", "matpick2528|")) or d=="matsubmit2528"):
            return subjects(cid,st.get("year","Tahun 1"))
        return previous_callback(cid,d)
    namespace["year"]=year
    namespace["subjects"]=subjects
    namespace["callback"]=callback
    print("CIKGULAJU_TELEGRAM_DLP_KP_MENU_READY", flush=True)
    return True
