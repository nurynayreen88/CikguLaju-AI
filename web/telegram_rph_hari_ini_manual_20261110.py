"""Telegram RPH Hari Ini from manually entered timetable; no image/PDF reader."""
import html

def install(rt):
    if getattr(rt, "CIKGULAJU_DAILY_MANUAL_ONLY_20261110", False):
        return True
    required = ("menu", "callback", "send", "_timetable_entries",
                "_today_rpt_suggestions_v25292", "_generate_daily_suggestions_v25292")
    if not all(callable(getattr(rt, k, None)) for k in required):
        return False
    old_menu, old_callback = rt.menu, rt.callback

    def timetable(cid, note=""):
        entries = rt._timetable_entries(cid)
        lines = ["📅 <b>JADUAL WAKTU SAYA</b>", "",
                 "✏️ Jadual waktu diisi sendiri oleh guru."]
        if note:
            lines.insert(0, html.escape(note))
        previous = None
        for e in entries:
            day = str(e.get("day") or "")
            if day != previous:
                lines.extend(["", "<b>" + html.escape(day) + "</b>"])
                previous = day
            lines.append("• " + html.escape("{}–{} • {} • {}".format(
                e.get("start") or "", e.get("end") or "",
                e.get("class_name") or "", e.get("subject") or "")))
        if not entries:
            lines.extend(["", "Belum ada jadual disimpan."])
        buttons = [[{"text": "✏️ Isi / Tambah Manual", "callback_data": "tt_add"}]]
        if entries:
            buttons.extend([
                [{"text": "🗑️ Padam Waktu", "callback_data": "tt_delete"}],
                [{"text": "🧹 Kosongkan Semua Jadual", "callback_data": "tt311_clear_ask"}],
                [{"text": "⚡ RPH Hari Ini", "callback_data": "todayrph272"}],
            ])
        buttons.extend([
            [{"text": "⬅️ Profil Saya", "callback_data": "account"}],
            [{"text": "🏠 Menu Utama", "callback_data": "home"}],
        ])
        return rt.send(cid, "\n".join(lines), buttons)

    def menu(cid, show_persistent=False):
        result = old_menu(cid, show_persistent=show_persistent)
        # Preserve existing referral/special-activity menu modifications.
        rt.send(cid, "⚡ <b>RPH Hari Ini</b>\n"
                    "Jadual waktu diisi secara manual, bukan dibaca daripada gambar.",
                [[{"text": "⚡ Buka RPH Hari Ini", "callback_data": "todayrph272"}],
                 [{"text": "✏️ Isi Jadual Waktu", "callback_data": "timetable"}]])
        return result

    def callback(cid, data):
        code = str(data or "")
        if code == "todayrph272":
            return rt._today_rpt_suggestions_v25292(cid)
        if code == "daily292_generate":
            ss = rt.state.setdefault(cid, {})
            if not ss.get("_daily_suggestions_v25292"):
                return rt._today_rpt_suggestions_v25292(cid)
            # Consume preview selection so a repeated tap cannot replay it.
            selected = ss.pop("_daily_suggestions_v25292")
            ss["_daily_suggestions_v25292"] = selected
            try:
                return rt._generate_daily_suggestions_v25292(cid)
            finally:
                ss.pop("_daily_suggestions_v25292", None)
        if code == "timetable":
            return timetable(cid)
        if code.startswith(("ttupload281_", "tt310_")):
            rt.state.setdefault(cid, {}).pop("waiting", None)
            return timetable(cid, "Fungsi baca/muat naik jadual waktu dimatikan.")
        return old_callback(cid, data)

    # Reject any old photo/PDF upload callbacks and document-handler entrypoints.
    if callable(getattr(rt, "_handle_timetable_upload_v25281", None)):
        def no_reader(cid, message):
            rt.state.setdefault(cid, {}).pop("waiting", None)
            return timetable(cid, "Sila isi jadual secara manual.")
        rt._handle_timetable_upload_v25281 = no_reader
    rt._timetable_menu = timetable
    rt.menu, rt.callback = menu, callback
    rt.CIKGULAJU_DAILY_MANUAL_ONLY_20261110 = True
    return True
