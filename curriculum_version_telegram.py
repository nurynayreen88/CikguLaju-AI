"""Install non-destructive Telegram curriculum selector around existing handlers."""
from curriculum_version_selector import KP2027, LEGACY, resolve_curriculum

def install(namespace):
    previous_callback=namespace["callback"]
    previous_subjects=namespace["subjects"]
    state=namespace["state"]
    send=namespace["send"]
    subjects_by_grade=namespace["SUBJECTS_BY_GRADE"]
    subject_label=namespace["SUBJECT_LABEL"]
    def choose(cid,label):
        st=state.setdefault(cid,{})
        st["year"]=label
        st.pop("subject",None)
        st.pop("topic",None)
        if label not in ("Tahun 1","Tingkatan 1"):
            st["curriculum_version"]=LEGACY
            return previous_subjects(cid,label)
        previous=st.get("curriculum_version",LEGACY)
        return send(cid,"📚 <b>"+label+"</b>\n\nPilih kurikulum:",[
            [{"text":("✅ " if previous==LEGACY else "")+"KSSR/KSSM Sedia Ada","callback_data":"cv_existing"}],
            [{"text":("✅ " if previous==KP2027 else "")+"Kurikulum Persekolahan 2027 (KP2027)","callback_data":"cv_kp2027"}],
            [{"text":"⬅️ Tahun/Tingkatan","callback_data":"choose_grade"}]])
    def subjects(cid,label):
        st=state.setdefault(cid,{})
        result=resolve_curriculum(st.get("curriculum_version"),label,st.get("subject"))
        if st.get("curriculum_version")==KP2027:
            # Display candidate subjects only; never route into legacy SK/SP.
            candidates=list(subjects_by_grade.get(label,()) or ())
            kb=[[{"text":"🚧 "+subject_label.get(sub,sub)+" — Dalam Pembinaan",
                  "callback_data":"cv_build_"+str(i)}]
                for i,sub in enumerate(candidates)]
            st["_kp2027_subject_candidates"]=candidates
            kb.extend([[{"text":"📖 Pratonton Kerangka Rasmi KP2027","callback_data":"cv_preview"}],
                       [{"text":"⬅️ Tukar Kurikulum","callback_data":"cv_choose"}],
                       [{"text":"🏠 Menu Utama","callback_data":"home"}]])
            return send(cid,"📚 <b>KP2027 • "+label+"</b>\\n\\n"
                        "Senarai subjek untuk persediaan katalog (tertakluk pengesahan dokumen rasmi). "
                        "Semua masih 🚧 Dalam Pembinaan; RPH belum boleh dijana.",kb)
        if not result["enabled"]:
            return send(cid,"⏳ KP2027 belum tersedia.",[[{"text":"⬅️ Tukar Kurikulum","callback_data":"cv_choose"}]])
        return previous_subjects(cid,label)
    def callback(cid,d):
        if d.startswith("year_"):
            return choose(cid,"Tahun "+d[5:])
        if d.startswith("form_"):
            return choose(cid,"Tingkatan "+d[5:])
        if d=="cv_choose":
            return choose(cid,state.setdefault(cid,{}).get("year","Tahun 1"))
        if d in ("cv_existing","cv_kp2027"):
            st=state.setdefault(cid,{})
            st["curriculum_version"]=LEGACY if d=="cv_existing" else KP2027
            return subjects(cid,st.get("year","Tahun 1"))
        st=state.setdefault(cid,{})
        if d.startswith("cv_build_"):
            try:
                idx=int(d[len("cv_build_"):])
                sub=st.get("_kp2027_subject_candidates",[])[idx]
                if idx<0: raise IndexError()
            except (ValueError,IndexError):
                return subjects(cid,st.get("year","Tahun 1"))
            return send(cid,"🚧 <b>"+subject_label.get(sub,sub)+" — KP2027</b>\\n"
                        "Dalam Pembinaan. Dokumen rasmi dan pemetaan SK/SP belum disahkan; "
                        "penjanaan RPH belum dibuka.",[
                        [{"text":"⬅️ Senarai Subjek KP2027","callback_data":"cv_subjects"}],
                        [{"text":"🏠 Menu Utama","callback_data":"home"}]])
        if d=="cv_preview":
            label=st.get("year","Tahun 1")
            return send(cid,
                "📖 <b>KP2027 • "+label+"</b>\\n\\n"
                "<b>Apa yang baharu?</b>\\n"
                "• Pelaksanaan berperingkat bermula pada 2027 untuk Tahun 1 dan Tingkatan 1.\\n"
                "• Kerangka memberi perhatian kepada pembentukan karakter, "
                "perkembangan kompetensi dan pembelajaran bermakna.\\n"
                "• Kandungan khusus setiap subjek akan dimasukkan selepas dokumen "
                "kurikulum rasminya disahkan.\\n\\n"
                "🚧 <b>Status CikguLaju:</b> Pratonton tersedia; SK/SP, pemetaan "
                "PdP dan janaan RPH KP2027 masih Dalam Pembinaan.\\n"
                "<i>Ringkasan berdasarkan kerangka KPM, bukan DSKP mata pelajaran.</i>",[
                [{"text":"📚 Lihat Subjek KP2027","callback_data":"cv_subjects"}],
                [{"text":"🏠 Menu Utama","callback_data":"home"}]])
        if d=="cv_subjects":
            return subjects(cid,st.get("year","Tahun 1"))
        if st.get("curriculum_version")==KP2027 and (d.startswith("sub_") or d.startswith("topic_") or d.startswith("st3|")):
            return subjects(cid,st.get("year","Tahun 1"))
        return previous_callback(cid,d)
    namespace["subjects"]=subjects
    namespace["callback"]=callback
    return True
