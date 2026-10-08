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
        # Temporary generic mode: verified SP is required; never invent SK.
        return [r for r in rows if any(x["standard_type"] == "SP" and x.get("standard_code") for x in r["_std"])]

    def menu(cid, page=0):
        ss = g["state"].setdefault(cid, {})
        subject = ss.get("subject", "")
        year = ss.get("year", "")
        rows = rows_for(year, subject)
        ss["_pjpk_v2616_rows"] = rows
        if not rows:
            reason = "Belum ada PdP dengan SP disahkan untuk pilihan ini."
            return g["send"](cid,
                "🚧 <b>PJPK belum boleh menjana RPH untuk pilihan ini.</b> " + reason,
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
            f"🏃 <b>{html.escape(subject)} • {html.escape(year)}</b>\\n\\nPilih PdP. RPH sementara menggunakan SP disahkan; SK yang belum disahkan tidak direka.",
            kb)

    def callback(cid, d):
        ss = g["state"].setdefault(cid, {})
        ds = str(d or "")
        if ds in ("sub_Pendidikan Jasmani", "sub_Pendidikan Kesihatan"):
            ss["subject"] = ds[4:]
            ss["task"] = "quick_material"
            ss["quick_material_flow"] = True
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
            if not row.get("_std"):
                return menu(cid)
            # Generic fallback is explicitly marked; do not reuse stale SK from a previous selection.
            ss["pjpk_generic_mode_v2616"] = True
            for key in ("selected_sk", "sk_code", "sk_text", "selected_sk_codes", "grouped_sk_codes", "grouped_sk_texts"):
                ss.pop(key, None)
            # Existing PM selection helper reads this cached row list.
            ss["_pm_pdp_rows_v2602"] = rows
            return g["_pm_commit_pdp_v2602"](cid, rows.index(row))
        return old_callback(cid, d)
    g["callback"] = callback
