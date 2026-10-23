"""Install non-destructive Telegram curriculum selector around existing handlers."""
from curriculum_version_selector import KP2027, LEGACY, resolve_curriculum

def install(namespace):
    previous_callback=namespace["callback"]
    previous_subjects=namespace["subjects"]
    state=namespace["state"]
    send=namespace["send"]
    def choose(cid,label):
        st=state.setdefault(cid,{})
        st["year"]=label
        st.pop("subject",None)
        st.pop("topic",None)
        if label not in ("Tahun 1","Tingkatan 1"):
            st["curriculum_version"]=LEGACY
            return previous_subjects(cid,label)
        previous=st.get("curriculum_version",LEGACY)
        return send(cid,"📚 <b>"+label+"</b>\\n\\nPilih kurikulum:",[
            [{"text":("✅ " if previous==LEGACY else "")+"KSSR/KSSM Sedia Ada","callback_data":"cv_existing"}],
            [{"text":("✅ " if previous==KP2027 else "")+"Kurikulum Persekolahan 2027 (KP2027)","callback_data":"cv_kp2027"}],
            [{"text":"⬅️ Tahun/Tingkatan","callback_data":"choose_grade"}]])
    def subjects(cid,label):
        st=state.setdefault(cid,{})
        result=resolve_curriculum(st.get("curriculum_version"),label,st.get("subject"))
        if not result["enabled"]:
            return send(cid,"⏳ <b>KP2027 belum tersedia.</b>\\nPemetaan subjek belum disahkan. SK/SP lama tidak akan digunakan.",[
                [{"text":"⬅️ Tukar Kurikulum","callback_data":"cv_choose"}],
                [{"text":"🏠 Menu Utama","callback_data":"home"}]])
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
        if st.get("curriculum_version")==KP2027 and (d.startswith("sub_") or d.startswith("topic_") or d.startswith("st3|")):
            return subjects(cid,st.get("year","Tahun 1"))
        return previous_callback(cid,d)
    namespace["subjects"]=subjects
    namespace["callback"]=callback
    return True
