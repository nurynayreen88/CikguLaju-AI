"""Show curriculum choices and DLP availability inside Telegram's RPH selectors."""
from html import escape
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory

from dlp_year2_rph import filename
from staging.dlp.year2.downloads import BY_SUBJECT

from curriculum_version_selector import KP2027, LEGACY, resolve_curriculum
from primary_language_subjects import PRIMARY_LANGUAGE_SUBJECTS


DLP = "dlp"
PPKI = "ppki"
DLP_YEARS = {
    f"cv_year{n}_dlp": f"Tahun {n}" for n in range(2, 7)
}
DLP_DOWNLOAD_YEAR = "Tahun 2"
DLP_2027_SCOPES = {
    "Tahun 3": {"SCIENCE_DLP": "d3", "MATH_DLP": "m3"},
    "Tahun 4": {"SCIENCE_DLP": "d4", "MATH_DLP": "m4"},
    "Tahun 5": {"SCIENCE_DLP": "d5", "MATH_DLP": "m5"},
    "Tahun 6": {"SCIENCE_DLP": "d6", "MATH_DLP": "m"},
}
PRIMARY_CURRICULA = {
    "cv_primary_kssr": (LEGACY, "KSSR"),
    "cv_primary_kp27": (KP2027, "KP2027"),
    "cv_primary_ppki": (PPKI, "Pendidikan Khas"),
}

DLP_SUBJECTS = {
    "cv_dlp_science": ("SCIENCE_DLP", "Science (DLP)"),
    "cv_dlp_math": ("MATH_DLP", "Mathematics (DLP)"),
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
    dev_subjects = namespace.get("_CIKGULAJU_DEV_SUBJECTS_V2617")
    if dev_subjects is not None:
        dev_subjects.update(dict.fromkeys(PRIMARY_LANGUAGE_SUBJECTS.values(), tuple(range(1, 7))))
    dlp_catalog = {code: module.units for code, module in BY_SUBJECT.items()}
    downloading = set()

    def published_scopes(year_label):
        if not namespace.get("CIKGULAJU_SK_2027_RPH_MENU"):
            return {}
        return DLP_2027_SCOPES.get(year_label, {})

    def dlp_subject_buttons(st, year_label):
        if not (_rph_flow(st) and st.get("curriculum_version") == LEGACY):
            return []
        scopes = published_scopes(year_label)
        return [{"text": name, "callback_data": key}
                for key, (code, name) in DLP_SUBJECTS.items()
                if year_label == DLP_DOWNLOAD_YEAR or code in scopes]

    def curriculum_menu(cid):
        reset_selection(cid, None)
        keyboard = [
            [{"text":label, "callback_data":key}]
            for key, (_, label) in PRIMARY_CURRICULA.items()
        ]
        keyboard.extend([
            [{"text":"⬅️ Pilih Peringkat Sekolah", "callback_data":"choose_grade"}],
            [{"text":"🏠 Menu Utama", "callback_data":"home"}],
        ])
        return send(cid, "🏫 <b>Sekolah Rendah</b>\n\nPilih kurikulum.", keyboard)

    def year(cid, level):
        if str(level).lower() != "primary" or not _rph_flow(state.get(cid, {})):
            return previous_year(cid, level)
        return curriculum_menu(cid)

    def reset_selection(cid, version):
        st = state.get(cid, {})
        # Drop stale lesson, standards and pending generation when switching stream.
        fresh = {key: st[key] for key in ("task", "quick_material_flow", "rph_mode", "_cid") if key in st}
        if version is not None:
            fresh["curriculum_version"] = version
        state[cid] = fresh
        return fresh

    def primary_years(cid, version, label):
        if version == LEGACY:
            keyboard = [
                [{"text":f"Tahun {n}", "callback_data":f"year_{n}"} for n in row]
                for row in ((1, 2), (3, 4), (5, 6))
            ]
        elif version == PPKI:
            from staging.ppki.catalog import YEARS
            keyboard = [[{"text": f"Tahun {number}", "callback_data": f"cv_ppki_year{number}"}]
                        for number in YEARS]
        else:
            keyboard = [[{"text":"Tahun 1 (KP Baharu)", "callback_data":"cv_year1_kp"}]]
        keyboard.extend([[{"text":"⬅️ Pilih Kurikulum", "callback_data":"level_primary"}],
                         [{"text":"🏠 Menu Utama", "callback_data":"home"}]])
        prompt = ("KSSR Pendidikan Khas (Masalah Pembelajaran) · Tahun 2–6.\nKP2027 Pendidikan Khas Tahun 1 belum tersedia.\n\nPilih tahun." if version == PPKI else "Pilih tahun.")
        return send(cid, f"📚 <b>{label}</b>\n\n{prompt}", keyboard)

    def choose_year_one_preview(cid):
        reset_selection(cid, KP2027)["year"] = "Tahun 1"
        return subjects(cid, "Tahun 1")

    def ppki_navigation(cid, st, action):
        from staging.ppki.catalog import (
            COMPONENT, MANIPULATIVE_COMPONENT, SUBJECT, UNIT, YEAR, YEARS, catalog,
            component_units, lesson_filename, selected_lesson,
        )
        from staging.ppki.render_pengurusan_kehidupan import render_lesson

        def show(label, prompt, choices, back):
            keyboard = [[{"text": title, "callback_data": key}] for title, key in choices]
            keyboard.append([{"text": "⬅️ Kembali", "callback_data": back}])
            return send(cid, f"<b>{escape(label)}</b>\n\n{prompt}", keyboard)

        if action in {f"year{number}" for number in YEARS}:
            year = int(action.removeprefix("year"))
            reset_selection(cid, PPKI)["year"] = f"Tahun {year}"
            source = catalog(component_units(year)[COMPONENT][0], year=year)
            return show(f"Pendidikan Khas · Tahun {year}", "Pilih subjek.",
                        [(source["subject"], "cv_ppki_subject")], "cv_primary_ppki")
        year = next((number for number in YEARS if st.get("year") == f"Tahun {number}"), None)
        if year is None:
            return primary_years(cid, PPKI, "Pendidikan Khas")
        units_by_component = component_units(year)
        if action == "subject":
            st["ppki_subject"] = SUBJECT
            st.pop("ppki_component", None)
            st.pop("ppki_unit", None)
            st.pop("ppki_lesson", None)
            components = [(catalog(units[0], year=year)["component"],
                           "cv_ppki_component_km" if code == MANIPULATIVE_COMPONENT else "cv_ppki_component")
                          for code, units in units_by_component.items()]
            source = catalog(units_by_component[COMPONENT][0], year=year)
            return show(source["subject"], "Pilih komponen.", components, f"cv_ppki_year{year}")
        if st.get("ppki_subject") != SUBJECT:
            return ppki_navigation(cid, st, f"year{year}")
        if action in ("component", "component_km"):
            component = MANIPULATIVE_COMPONENT if action == "component_km" else COMPONENT
            if component not in units_by_component:
                return ppki_navigation(cid, st, "subject")
            st["ppki_component"] = component
            st.pop("ppki_unit", None)
            st.pop("ppki_lesson", None)
            units = units_by_component[component]
            choices = [(catalog(unit, year=year)["unit"], f"cv_ppki_unit_{unit}") for unit in units]
            return show(catalog(units[0], year=year)["component"], "Pilih unit.", choices, "cv_ppki_subject")
        component = st.get("ppki_component")
        if component is True:  # Preserve existing Pengurusan Diri selections.
            component = COMPONENT
        if component not in units_by_component:
            return ppki_navigation(cid, st, "subject")
        units = units_by_component[component]
        back_to_component = "component_km" if component == MANIPULATIVE_COMPONENT else "component"
        if action == "unit" or action.startswith("unit_"):
            unit = (UNIT if year == YEAR else units[0]) if action == "unit" else action.removeprefix("unit_")
            if unit not in units:
                return ppki_navigation(cid, st, back_to_component)
            source = catalog(unit, year=year)
            st["ppki_unit"] = unit
            st.pop("ppki_lesson", None)
            choices = [(f"PdP {row['pdp']} · {row['title']}", f"cv_ppki_lesson_{row['pdp']}")
                       for row in source["lessons"]]
            return show(source["unit"], "Pilih PdP.", choices, f"cv_ppki_{back_to_component}")
        command, _, number = action.partition("_")
        unit = st.get("ppki_unit")
        lesson = selected_lesson(unit, number, year=year) if unit in units else None
        if lesson is None:
            return ppki_navigation(cid, st, back_to_component)
        if command == "lesson":
            st["ppki_lesson"] = number
            return show(lesson["title"], "Pilih format RPH.",
                        [("⬇️ Muat Turun Word", f"cv_ppki_word_{number}"),
                         ("⬇️ Muat Turun PDF", f"cv_ppki_pdf_{number}")], f"cv_ppki_unit_{unit}")
        if command not in ("word", "pdf") or st.get("ppki_lesson") != number:
            return ppki_navigation(cid, st, f"unit_{unit}")
        if cid in downloading:
            return send(cid, "Fail sedang dijana. Sila tunggu sebentar.")
        downloading.add(cid)
        try:
            if not namespace["_credit_gate"](cid, st):
                return
            extension = "docx" if command == "word" else "pdf"
            with TemporaryDirectory(prefix="cikgulaju-ppki-") as directory:
                path = Path(directory) / lesson_filename(number, command, year=year)
                path.write_bytes(render_lesson(catalog(unit, year=year), lesson, extension, {}))
                result = namespace["send_document"](cid, str(path), escape(lesson["title"]))
            if namespace["_telegram_delivery_ok_v25279"](result):
                return result
        except Exception:
            getLogger(__name__).exception("PPKI document delivery failed for %s", number)
        finally:
            st.pop("_free_generation_pending_v25282", None)
            downloading.remove(cid)
        return send(cid, "Fail PPKI belum berjaya dihantar. Pilih format untuk cuba semula.")

    def dlp_units(cid, subject_key):
        code, name = DLP_SUBJECTS[subject_key]
        st = state[cid]
        st["dlp_subject"] = subject_key
        st.pop("dlp_unit", None)
        st.pop("dlp_lesson", None)
        keyboard = [[{"text": unit["title"], "callback_data": "cv_dlp_unit_" + unit["id"]}]
                    for unit in dlp_catalog[code]]
        keyboard.append([{"text": "⬅️ Pilih Subjek", "callback_data": "back_subjects"}])
        return send(cid, f"<b>{name} · Year 2 SK</b>\n\nPilih unit.", keyboard)

    def dlp_lessons(cid, subject_key, unit):
        state[cid]["dlp_unit"] = unit["id"]
        state[cid].pop("dlp_lesson", None)
        keyboard = [[{"text": f"{lesson['numbered_label']} · {lesson['title']}"[:64],
                      "callback_data": "cv_dlp_rph_" + lesson["id"]}]
                    for lesson in unit["lessons"]]
        keyboard.append([{"text": "⬅️ Pilih Unit", "callback_data": subject_key}])
        return send(cid, f"<b>{escape(unit['title'])}</b>\nPilih tajuk RPH.", keyboard)

    def dlp_lesson(cid, subject_key, unit, lesson):
        _, name = DLP_SUBJECTS[subject_key]
        state[cid]["dlp_lesson"] = lesson["id"]
        keyboard = [[
            {"text": "⬇️ Muat Turun Word", "callback_data": "cv_dlp_word_" + lesson["id"]},
            {"text": "⬇️ Muat Turun PDF", "callback_data": "cv_dlp_pdf_" + lesson["id"]},
        ], [{"text": "⬅️ Pilih Tajuk RPH", "callback_data": "cv_dlp_unit_" + unit["id"]}]]
        return send(cid, f"<b>{escape(lesson['title'])}</b>\n{name} · Year 2 SK\n\nPilih format fail.", keyboard)

    def download_dlp(cid, st, fmt, lesson_id):
        if not (_rph_flow(st) and st.get("curriculum_version") == DLP
                and st.get("year") == DLP_DOWNLOAD_YEAR and st.get("dlp_lesson") == lesson_id):
            return send(cid, "Sila pilih tajuk RPH DLP semula.")
        subject_key = st.get("dlp_subject")
        if subject_key not in DLP_SUBJECTS:
            return send(cid, "Sila pilih subjek DLP semula.")
        code, _ = DLP_SUBJECTS[subject_key]
        module = BY_SUBJECT[code]
        plan = module.resolve_download(st.get("dlp_unit"), lesson_id)
        if plan is None:
            return send(cid, "RPH DLP ini tidak tersedia. Sila pilih tajuk semula.")
        if cid in downloading:
            return send(cid, "Fail sedang dijana. Sila tunggu sebentar.")
        downloading.add(cid)
        try:
            if not namespace["_credit_gate"](cid, st):
                return
            _, lesson = plan
            teacher = {"class": "", "date": "", "time": "", "students": ""}
            with TemporaryDirectory(prefix="cikgulaju-dlp-") as directory:
                path = Path(directory) / filename(lesson_id, fmt)
                path.write_bytes(module.render_download(lesson, fmt, teacher))
                result = namespace["send_document"](cid, str(path), escape(lesson["title"]))
            if namespace["_telegram_delivery_ok_v25279"](result):
                return result
        except Exception:
            getLogger(__name__).exception("DLP document delivery failed for %s", lesson_id)
        finally:
            st.pop("_free_generation_pending_v25282", None)
            downloading.remove(cid)
        return send(cid, "Fail DLP belum berjaya dihantar. Pilih format untuk cuba semula.")

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
        if st.get("curriculum_version") == PPKI:
            from staging.ppki.catalog import YEAR
            saved_year = str(st.get("year", "")).removeprefix("Tahun ")
            return ppki_navigation(cid, st, f"year{saved_year or YEAR}")
        if st.get("curriculum_version") == DLP:
            reset_selection(cid, LEGACY)["year"] = label
            return previous_subjects(cid, label)
        result=resolve_curriculum(st.get("curriculum_version"),label,st.get("subject"))
        if st.get("curriculum_version")==KP2027 and label in ("Tahun 1", "Tingkatan 1"):
            # Display candidate subjects only; never route into legacy SK/SP.
            candidates=list(subjects_by_grade.get(label,()) or ())
            if label=="Tahun 1":
                # Temporary KP2027 menu-only hide; preserve legacy and stored data.
                hidden={"BC","BT","Bahasa Cina","Bahasa Tamil"}
                candidates=list(dict.fromkeys(
                    "Alam dan Manusia" if subject_label.get(sub, sub) == "Sains" else sub
                    for sub in candidates
                    if sub not in hidden and subject_label.get(sub, sub) not in hidden
                ))
            kb=[[{"text":subject_label.get(sub,sub)+" — Akan Datang",
                  "callback_data":"cv_build_"+str(i)}]
                for i,sub in enumerate(candidates)]
            st["_kp2027_subject_candidates"]=candidates
            kb.extend([[{"text":"📖 Pratonton Kerangka Rasmi KP2027","callback_data":"cv_preview"}],
                       [{"text":"⬅️ Pilih Tahun","callback_data":"cv_choose"}],
                       [{"text":"🏠 Menu Utama","callback_data":"home"}]])
            notice = (" Komponen Sains Tahun 1 berada dalam Alam dan Manusia." if label == "Tahun 1" else "")
            return send(cid,"📚 <b>"+label+" (KP Baharu)</b>\n\n"
                        "Bahan Kurikulum Persekolahan 2027 sedang disemak. Janaan RPH berstatus Akan Datang."
                        + notice, kb)
        if not result["enabled"]:
            return send(cid,"⏳ KP2027 belum tersedia.",[[{"text":"⬅️ Tukar Kurikulum","callback_data":"cv_choose"}]])
        return previous_subjects(cid,label)

    def callback(cid,d):
        st=state.setdefault(cid,{})
        version = st.get("curriculum_version")
        if d == "cv_primary_dlp":
            d = "cv_primary_kssr"
        if d in PRIMARY_CURRICULA:
            if not _rph_flow(st):
                return year(cid, "primary")
            version, label = PRIMARY_CURRICULA[d]
            reset_selection(cid, version)
            return primary_years(cid, version, label)
        if d.startswith("cv_ppki_"):
            if _rph_flow(st) and version == PPKI:
                return ppki_navigation(cid, st, d.removeprefix("cv_ppki_"))
            return year(cid, "primary")
        if d == "cv_year1_kp":
            if _rph_flow(st) and version == KP2027:
                return choose_year_one_preview(cid)
            return year(cid, "primary")
        if d == "cv_year1_dlp":
            return year(cid, "primary")
        if d in DLP_YEARS:
            if _rph_flow(st) and version in (LEGACY, DLP):
                year_label = DLP_YEARS[d]
                reset_selection(cid, LEGACY)["year"] = year_label
                return subjects(cid, year_label)
            return year(cid, "primary")
        if d in DLP_SUBJECTS:
            year_label = st.get("year")
            if not (_rph_flow(st) and version in (LEGACY, DLP)
                    and year_label in DLP_YEARS.values()):
                return year(cid, "primary")
            code, _ = DLP_SUBJECTS[d]
            scope = published_scopes(year_label).get(code)
            if year_label != DLP_DOWNLOAD_YEAR and not scope:
                return subjects(cid, year_label)
            reset_selection(cid, DLP)["year"] = year_label
            if scope:
                return namespace["callback"](cid, f"sk27:dlp:{scope}")
            return dlp_units(cid, d)
        if d.startswith(("cv_dlp_word_", "cv_dlp_pdf_")):
            _, _, fmt, lesson_id = d.split("_", 3)
            return download_dlp(cid, st, fmt, lesson_id)
        if d.startswith(("cv_dlp_unit_", "cv_dlp_rph_")):
            if not (_rph_flow(st) and st.get("year") == DLP_DOWNLOAD_YEAR and version == DLP):
                return year(cid, "primary")
            subject_key = st.get("dlp_subject")
            if subject_key not in DLP_SUBJECTS:
                return subjects(cid, DLP_DOWNLOAD_YEAR)
            code, _ = DLP_SUBJECTS[subject_key]
            groups = dlp_catalog[code]
            if d.startswith("cv_dlp_unit_"):
                unit = next((row for row in groups if row["id"] == d[len("cv_dlp_unit_"):]), None)
                if unit:
                    return dlp_lessons(cid, subject_key, unit)
            else:
                unit = next((row for row in groups if row["id"] == st.get("dlp_unit")), None)
                if unit:
                    lesson = next((row for row in unit["lessons"] if row["id"] == d[len("cv_dlp_rph_"):]), None)
                    if lesson:
                        return dlp_lesson(cid, subject_key, unit, lesson)
            return dlp_units(cid, subject_key)
        if d.startswith("year_"):
            if _rph_flow(st) and version != LEGACY:
                return curriculum_menu(cid)
            return choose(cid,"Tahun "+d[5:])
        if d.startswith("form_"):
            return choose(cid,"Tingkatan "+d[5:])
        if d=="cv_choose":
            label = st.get("year","Tahun 1")
            if label=="Tingkatan 1" or not _rph_flow(st):
                return choose(cid,label)
            if version == KP2027:
                reset_selection(cid, KP2027)
                return primary_years(cid, KP2027, "KP2027")
            return curriculum_menu(cid)
        if d in ("cv_existing","cv_kp2027"):
            if _rph_flow(st) and st.get("year") != "Tingkatan 1":
                return callback(cid, "cv_primary_kssr" if d=="cv_existing" else "cv_primary_kp27")
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
            if version != KP2027 or not st.get("year"):
                return year(cid, "primary")
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
            if version != KP2027 or not st.get("year"):
                return year(cid, "primary")
            return subjects(cid,st["year"])
        if d=="back_subjects" and version in (KP2027, DLP, PPKI) and st.get("year"):
            return subjects(cid,st["year"])
        if version in (KP2027, DLP, PPKI) and (
                d.startswith(("sub_", "topic_", "st3|", "matpick2528|")) or d=="matsubmit2528"):
            if not st.get("year"):
                return curriculum_menu(cid)
            return subjects(cid,st["year"])
        return previous_callback(cid,d)
    namespace["_cikgulaju_dlp_subject_buttons"]=dlp_subject_buttons
    namespace["year"]=year
    namespace["subjects"]=subjects
    namespace["callback"]=callback
    print("CIKGULAJU_TELEGRAM_DLP_KP_MENU_READY", flush=True)
    return True
