"""Staging-only PJPK menu integration. Keeps legacy DB_PATH unchanged."""
def install(g):
    import html
    import sqlite3
    from pathlib import Path
    from scripts.pjpk_v26_16_adapter import ready_pdp

    subjects = (("🏃 Pendidikan Jasmani", "Pendidikan Jasmani"),
                ("❤️ Pendidikan Kesihatan", "Pendidikan Kesihatan"))
    old_callback = g["callback"]
    g["SUBJECTS"] = list(g["SUBJECTS"])
    for label, subject in subjects:
        if not any(value == subject for _, value in g["SUBJECTS"]):
            g["SUBJECTS"].append((label, subject))
        g["SUBJECT_LABEL"][subject] = label
        for year in range(1, 7):
            grade = f"Tahun {year}"
            vals = list(g["SUBJECTS_BY_GRADE"].get(grade, []) or [])
            if subject not in vals:
                vals.append(subject)
            g["SUBJECTS_BY_GRADE"][grade] = vals

    def database_path():
        path = Path(__file__).resolve().parents[1] / "CikguLaju_Curriculum_Master_v26_16_PJPK_SAFE_RELEASE.db"
        if path.exists():
            return path
        # Rebuild from versioned parts without replacing existing databases.
        from scripts.rebuild_pm_pjpk_v26_16 import main as rebuild
        try:
            rebuild()
        except (OSError, RuntimeError, SystemExit) as exc:
            print("PJPK v26.16 unavailable:", exc, flush=True)
        return path

    def rows_for(year, subject):
        path = database_path()
        rows = ready_pdp(year, subject, db_path=path)
        if not rows:
            return []
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as con:
            con.row_factory = sqlite3.Row
            for row in rows:
                row["_std"] = [dict(s) for s in con.execute(
                    """SELECT standard_type,standard_code,standard_text,sequence_no
                    FROM rpt_entry_standards WHERE rpt_entry_id=? AND verified=1
                    ORDER BY CASE standard_type WHEN 'SK' THEN 0 ELSE 1 END,sequence_no,id""",
                    (row["id"],))]
        # No RPH without verified SK and SP.
        return [r for r in rows if any(x["standard_type"] == "SK" for x in r["_std"])
                and any(x["standard_type"] == "SP" for x in r["_std"])]

    def menu(cid, page=0):
        ss = g["state"].setdefault(cid, {})
        subject = ss.get("subject", "")
        year = ss.get("year", "")
        rows = rows_for(year, subject)
        ss["_pjpk_v2616_rows"] = rows
        if not rows:
            return g["send"](cid,
                "🚧 <b>PdP PJPK untuk pilihan ini belum lengkap disahkan.</b> Data belum siap tidak digunakan untuk RPH.",
                [[{"text": "⬅️ Tukar Subjek", "callback_data": "choose_grade"}],
                 [{"text": "🏠 Menu Utama", "callback_data": "home"}]])
        page = max(0, int(page))
        start, per = page * 12, 12
        kb = []
        for i, row in enumerate(rows[start:start + per], start):
            label = f"PdP {row['sequence_no']} • {row.get('unit_title') or row.get('topic') or ''}"
            kb.append([{"text": label[:60], "callback_data": f"pjpk2616pdp|{i}"}])
        nav = []
        if page:
            nav.append({"text": "⬅️", "callback_data": f"pjpk2616page|{page-1}"})
        if start + per < len(rows):
            nav.append({"text": "➡️", "callback_data": f"pjpk2616page|{page+1}"})
        if nav:
            kb.append(nav)
        kb.append([{"text": "⬅️ Tukar Subjek", "callback_data": "choose_grade"}])
        return g["send"](cid,
            f"🏃 <b>{html.escape(subject)} • {html.escape(year)}</b>\\n\\nPilih PdP yang telah disahkan.",
            kb)

    def commit_pdp(cid, row):
        """Populate the normal RPH flow from a PJPK row with verified SK and SP."""
        ss = g["state"].setdefault(cid, {})
        sks, sktexts, sps, sptexts = [], [], [], []
        for item in row.get("_std") or []:
            code = str(item.get("standard_code") or "").strip()
            text = str(item.get("standard_text") or "").strip()
            if not code:
                continue
            if item.get("standard_type") == "SK" and code not in sks:
                sks.append(code)
                sktexts.append(text)
            elif item.get("standard_type") == "SP" and code not in sps:
                sps.append(code)
                sptexts.append(text)
        if not sks or not sps:
            return menu(cid)
        for key in (
            "selected_sk", "sk_code", "sk_text", "selected_sk_codes",
            "grouped_sk_codes", "grouped_sk_texts", "selected_sp", "sp_code",
            "sp_text", "selected_sp_codes", "grouped_sp_codes", "grouped_sp_texts",
            "topic", "subtopic", "selected_topic_index", "topic_list",
            "quick_content_v2391", "_quick_tb_rows_v2391",
            "_quick_rpt_rows_content_v2391", "rpt_entry_id", "pdp_no",
            "lesson_no", "theme", "unit", "unit_title", "skill_focus",
            "rpt_activity_note", "rpt_assessment_note",
        ):
            ss.pop(key, None)
        ss["task"] = "quick_material"
        ss["quick_material_flow"] = True
        ss["assessment_mode"] = "formative"
        ss["rph_mode"] = "fast_rpt"
        ss["_quick_selected_rpt_row_v2388"] = dict(row)
        ss["quick_rpt_row"] = dict(row)
        ss["rpt_entry_id"] = row.get("id")
        ss["pdp_no"] = row.get("sequence_no")
        ss["lesson_no"] = str(row.get("sequence_no") or "")
        ss["theme"] = str(row.get("theme") or "").strip()
        ss["unit"] = str(row.get("unit_title") or "").strip()
        ss["unit_title"] = ss["unit"]
        ss["topic"] = str(row.get("topic") or row.get("skill_focus") or row.get("unit_title") or "").strip()
        ss["subtopic"] = str(row.get("subtopic") or "").strip()
        ss["skill_focus"] = str(row.get("skill_focus") or "").strip()
        ss["quick_content_v2391"] = ss["unit"] or ss["topic"]
        ss["rpt_activity_note"] = str(row.get("activity_note") or "").strip()
        ss["rpt_assessment_note"] = str(row.get("assessment_note") or "").strip()
        ss["grouped_sk_codes"] = sks
        ss["selected_sk_codes"] = sks
        ss["grouped_sk_texts"] = sktexts
        ss["grouped_sp_codes"] = sps[:4]
        ss["selected_sp_codes"] = sps[:4]
        ss["grouped_sp_texts"] = sptexts[:4]
        ss["selected_sk"] = sks[0]
        ss["sk_code"] = sks[0]
        ss["sk_text"] = sktexts[0]
        ss["selected_sp"] = sps[0]
        ss["sp_code"] = sps[0]
        ss["sp_text"] = sptexts[0]
        lesson_to_class = g.get("_lesson_to_class_v2439")
        if callable(lesson_to_class):
            return lesson_to_class(cid)
        return g["send"](cid, "⚠️ Laluan pemilihan kelas untuk RPH belum tersedia.",
                           [[{"text": "🏠 Menu Utama", "callback_data": "home"}]])

    def callback(cid, d):
        ss = g["state"].setdefault(cid, {})
        ds = str(d or "")
        if ds in ("sub_Pendidikan Jasmani", "sub_Pendidikan Kesihatan"):
            ss["subject"] = ds[4:]
            ss["task"] = "quick_material"
            ss["quick_material_flow"] = True
            ss["assessment_mode"] = "formative"
            for key in ("selected_sk", "sk_code", "sk_text", "selected_sk_codes",
                        "grouped_sk_codes", "grouped_sk_texts", "selected_sp", "sp_code",
                        "sp_text", "selected_sp_codes", "grouped_sp_codes", "grouped_sp_texts",
                        "_quick_selected_rpt_row_v2388", "quick_rpt_row"):
                ss.pop(key, None)
            return menu(cid)
        if ds.startswith("pjpk2616page|") and ss.get("subject") in (s for _, s in subjects):
            try:
                return menu(cid, int(ds.split("|", 1)[1]))
            except ValueError:
                return menu(cid)
        if ds.startswith("pjpk2616pdp|") and ss.get("subject") in (s for _, s in subjects):
            rows = ss.get("_pjpk_v2616_rows") or rows_for(ss.get("year"), ss.get("subject"))
            try:
                row = rows[int(ds.split("|", 1)[1])]
            except (ValueError, IndexError):
                return menu(cid)
            return commit_pdp(cid, row)
        return old_callback(cid, d)
    g["callback"] = callback
