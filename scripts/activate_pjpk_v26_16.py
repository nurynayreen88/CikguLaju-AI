"""Opt-in PJPK menu integration for the v26.16 verified safe-release dataset.

Keeps the legacy DB_PATH unchanged. Only entries that pass the read-only
release view and contain verified SP are offered. This module is not activated
by importing it; the host application must explicitly call install(globals()).
"""
def install(g):
    import html
    import sqlite3
    from pathlib import Path
    from scripts.pjpk_v26_16_adapter import ready_pdp

    subjects = (("🏃 Pendidikan Jasmani", "Pendidikan Jasmani"),
                ("❤️ Pendidikan Kesihatan", "Pendidikan Kesihatan"))
    old_callback = g["callback"]
    rebuild_failed = [False]

    g["SUBJECTS"] = list(g["SUBJECTS"])
    for label, subject in subjects:
        if not any(value == subject for _, value in g["SUBJECTS"]):
            g["SUBJECTS"].append((label, subject))
        g["SUBJECT_LABEL"][subject] = label
        for year in range(1, 7):
            grade = f"Tahun {year}"
            values = list(g["SUBJECTS_BY_GRADE"].get(grade, []) or [])
            if subject not in values:
                values.append(subject)
            g["SUBJECTS_BY_GRADE"][grade] = values

    def database_path():
        path = Path(__file__).resolve().parents[1] / "CikguLaju_Curriculum_Master_v26_16_PJPK_SAFE_RELEASE.db"
        if path.exists() or rebuild_failed[0]:
            return path
        from scripts.rebuild_pm_pjpk_v26_16 import main as rebuild
        try:
            rebuild()
        except (OSError, RuntimeError, SystemExit, ImportError, sqlite3.Error) as exc:
            rebuild_failed[0] = True
            print("PJPK v26.16 unavailable:", exc, flush=True)
        return path

    def rows_for(year, subject):
        path = database_path()
        rows = ready_pdp(year, subject, db_path=path)
        if not rows:
            return []
        try:
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as con:
                con.row_factory = sqlite3.Row
                for row in rows:
                    row["_std"] = [dict(item) for item in con.execute(
                        """SELECT standard_type,standard_code,standard_text,sequence_no,verified
                        FROM rpt_entry_standards WHERE rpt_entry_id=? AND verified=1
                        ORDER BY CASE standard_type WHEN 'SK' THEN 0 ELSE 1 END,sequence_no,id""",
                        (row["id"],))]
        except (sqlite3.Error, OSError) as exc:
            print("PJPK standards lookup failed closed:", exc, flush=True)
            return []
        # Never invent SK; a verified SP is mandatory for RPH selection.
        return [row for row in rows if any(
            item["standard_type"] == "SP" and str(item.get("standard_code") or "").strip()
            for item in row["_std"]
        )]

    def menu(cid, page=0):
        state = g["state"].setdefault(cid, {})
        subject = state.get("subject", "")
        year = state.get("year", "")
        rows = rows_for(year, subject)
        state["_pjpk_v2616_rows"] = rows
        if not rows:
            return g["send"](cid,
                "🚧 <b>PdP PJPK untuk pilihan ini belum disahkan sepenuhnya.</b> Data belum siap tidak digunakan untuk RPH.",
                [[{"text": "⬅️ Tukar Subjek", "callback_data": "choose_grade"}],
                 [{"text": "🏠 Menu Utama", "callback_data": "home"}]])
        page = max(0, int(page))
        start, per_page = page * 12, 12
        keyboard = []
        for index, row in enumerate(rows[start:start + per_page], start):
            label = f"PdP {row['sequence_no']} • {row.get('unit_title') or row.get('topic') or ''}"
            keyboard.append([{"text": label[:60], "callback_data": f"pjpk2616pdp|{index}"}])
        navigation = []
        if page:
            navigation.append({"text": "⬅️", "callback_data": f"pjpk2616page|{page - 1}"})
        if start + per_page < len(rows):
            navigation.append({"text": "➡️", "callback_data": f"pjpk2616page|{page + 1}"})
        if navigation:
            keyboard.append(navigation)
        keyboard.append([{"text": "⬅️ Tukar Subjek", "callback_data": "choose_grade"}])
        return g["send"](cid,
            f"🏃 <b>{html.escape(subject)} • {html.escape(year)}</b>\n\nPilih PdP yang telah disahkan. SK yang belum disahkan tidak direka.",
            keyboard)

    def commit_pdp(cid, row):
        """Load a selected verified row into the existing RPH lesson flow."""
        state = g["state"].setdefault(cid, {})
        sk_codes, sk_texts, sp_codes, sp_texts = [], [], [], []
        for item in row.get("_std") or []:
            code = str(item.get("standard_code") or "").strip()
            text = str(item.get("standard_text") or "").strip()
            if not code:
                continue
            if item.get("standard_type") == "SK" and code not in sk_codes:
                sk_codes.append(code)
                sk_texts.append(text)
            elif item.get("standard_type") == "SP" and code not in sp_codes:
                sp_codes.append(code)
                sp_texts.append(text)
        if not sp_codes:
            return menu(cid)

        stale_keys = (
            "selected_sk", "sk_code", "sk_text", "selected_sk_codes",
            "grouped_sk_codes", "grouped_sk_texts", "selected_sp", "sp_code",
            "sp_text", "selected_sp_codes", "grouped_sp_codes", "grouped_sp_texts",
            "topic", "subtopic", "selected_topic_index", "topic_list",
            "quick_content_v2391", "_quick_tb_rows_v2391",
            "_quick_rpt_rows_content_v2391", "rpt_entry_id", "pdp_no",
            "lesson_no", "theme", "unit", "unit_title", "skill_focus",
            "rpt_activity_note", "rpt_assessment_note",
            "_quick_selected_rpt_row_v2388", "quick_rpt_row",
        )
        for key in stale_keys:
            state.pop(key, None)

        state["pjpk_generic_mode_v2616"] = not bool(sk_codes)
        state["task"] = "quick_material"
        state["quick_material_flow"] = True
        state["assessment_mode"] = "formative"
        state["rph_mode"] = "fast_rpt"
        state["_quick_selected_rpt_row_v2388"] = dict(row)
        state["quick_rpt_row"] = dict(row)
        state["rpt_entry_id"] = row.get("id")
        state["pdp_no"] = row.get("sequence_no")
        state["lesson_no"] = str(row.get("sequence_no") or "")
        state["theme"] = str(row.get("theme") or "").strip()
        state["unit"] = str(row.get("unit_title") or "").strip()
        state["unit_title"] = state["unit"]
        state["topic"] = str(row.get("topic") or row.get("skill_focus") or row.get("unit_title") or "").strip()
        state["subtopic"] = str(row.get("subtopic") or "").strip()
        state["skill_focus"] = str(row.get("skill_focus") or "").strip()
        state["quick_content_v2391"] = state["unit"] or state["topic"]
        state["rpt_activity_note"] = str(row.get("activity_note") or "").strip()
        state["rpt_assessment_note"] = str(row.get("assessment_note") or "").strip()
        state["grouped_sk_codes"] = sk_codes
        state["selected_sk_codes"] = sk_codes
        state["grouped_sk_texts"] = sk_texts
        state["grouped_sp_codes"] = sp_codes[:4]
        state["selected_sp_codes"] = sp_codes[:4]
        state["grouped_sp_texts"] = sp_texts[:4]
        if sk_codes:
            state["selected_sk"] = sk_codes[0]
            state["sk_code"] = sk_codes[0]
            state["sk_text"] = sk_texts[0]
        state["selected_sp"] = sp_codes[0]
        state["sp_code"] = sp_codes[0]
        state["sp_text"] = sp_texts[0]

        lesson_to_class = g.get("_lesson_to_class_v2439")
        if callable(lesson_to_class):
            return lesson_to_class(cid)
        return g["send"](cid,
            "⚠️ Laluan pemilihan kelas untuk RPH belum tersedia; data PJPK tidak dihantar ke laluan lain.",
            [[{"text": "🏠 Menu Utama", "callback_data": "home"}]])

    def callback(cid, data):
        state = g["state"].setdefault(cid, {})
        value = str(data or "")
        if value in ("sub_Pendidikan Jasmani", "sub_Pendidikan Kesihatan"):
            state["subject"] = value[4:]
            state["task"] = "quick_material"
            state["quick_material_flow"] = True
            state["assessment_mode"] = "formative"
            for key in ("selected_sk", "sk_code", "sk_text", "selected_sk_codes",
                        "grouped_sk_codes", "grouped_sk_texts", "selected_sp", "sp_code",
                        "sp_text", "selected_sp_codes", "grouped_sp_codes", "grouped_sp_texts",
                        "_quick_selected_rpt_row_v2388", "quick_rpt_row"):
                state.pop(key, None)
            return menu(cid)
        if value.startswith("pjpk2616page|") and state.get("subject") in (s for _, s in subjects):
            try:
                return menu(cid, int(value.split("|", 1)[1]))
            except ValueError:
                return menu(cid)
        if value.startswith("pjpk2616pdp|") and state.get("subject") in (s for _, s in subjects):
            rows = state.get("_pjpk_v2616_rows") or rows_for(state.get("year"), state.get("subject"))
            try:
                row = rows[int(value.split("|", 1)[1])]
            except (ValueError, IndexError):
                return menu(cid)
            return commit_pdp(cid, row)
        return old_callback(cid, data)

    g["callback"] = callback
