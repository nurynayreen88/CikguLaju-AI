"""Telegram RPH Hari Ini: teacher-entered timetable, verified daily material only.

Never enable timetable photo/PDF reading. Respect the existing RPH / trial
entitlement path and never record a progress checkpoint for a failed delivery.
"""
from __future__ import annotations

import html


def install(rt):
    if getattr(rt, "CIKGULAJU_DAILY_MANUAL_ONLY_20261110", False):
        return True
    required = ("menu", "callback", "send", "_timetable_entries",
                "_today_rpt_suggestions_v25292", "_today_rows_v25272",
                "_entry_with_subject_v25294", "_daily_candidate_v25292",
                "_generate_one_quick_rph_v25278", "_generate_calendar_row_v25293",
                "_telegram_delivery_ok_v25279")
    if not all(callable(getattr(rt, k, None)) for k in required):
        return False
    if not isinstance(getattr(rt, "state", None), dict):
        return False
    old_callback = rt.callback

    def timetable(cid, note=""):
        entries = rt._timetable_entries(cid)
        lines = ["📅 <b>JADUAL WAKTU SAYA</b>", "",
                 "✏️ Jadual waktu diisi sendiri oleh guru."]
        if note:
            lines.insert(0, html.escape(note))
        previous = None
        for entry in entries:
            day = str(entry.get("day") or "")
            if day != previous:
                lines.extend(["", "<b>" + html.escape(day) + "</b>"])
                previous = day
            lines.append("• " + html.escape("{}–{} • {} • {}".format(
                entry.get("start") or "", entry.get("end") or "",
                entry.get("class_name") or "", entry.get("subject") or "")))
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

    def generate_daily(cid):
        ss = rt.state.setdefault(cid, {})
        # Atomic pop prevents double tapping the same cached preview on one worker.
        selected = ss.pop("_daily_suggestions_v25292", None)
        if not selected:
            return rt._today_rpt_suggestions_v25292(cid)
        current_day, current_rows = rt._today_rows_v25272(cid)
        valid = {(str(e.get("day") or ""), str(e.get("start") or ""),
                  str(e.get("end") or ""), str(e.get("class_name") or ""),
                  str(e.get("subject") or "")) for _i, e in current_rows}
        results = []
        seen_slots, successful_lessons = set(), set()
        try:
            for item in selected:
                entry = dict(item.get("entry") or {})
                slot = (str(entry.get("day") or ""), str(entry.get("start") or ""),
                        str(entry.get("end") or ""), str(entry.get("class_name") or ""),
                        str(entry.get("_timetable_subject") or entry.get("subject") or ""))
                if slot not in valid or slot in seen_slots:
                    results.append((entry, False, "slot jadual telah berubah/berulang"))
                    continue
                seen_slots.add(slot)
                # Re-resolve at execution time: a successful first slot may move
                # the checkpoint and the next slot must use the NEXT verified PdP.
                row, source = rt._daily_candidate_v25292(cid, entry)
                if not row:
                    results.append((entry, False, source))
                    continue
                subj = str(row.get("_resolved_subject_v25294") or entry.get("subject") or "")
                canonical = rt._entry_with_subject_v25294(entry, subj)
                seq = str(row.get("_sequence_no") or row.get("lesson_no") or row.get("sequence_no") or "")
                lesson_key = (str(canonical.get("class_name") or "").casefold(),
                              subj.casefold(), seq)
                if lesson_key in successful_lessons:
                    results.append((canonical, False, "PdP/Lesson yang sama sudah dijana"))
                    continue
                if not seq:
                    results.append((canonical, False, "Nombor PdP/Lesson belum disahkan"))
                    continue
                ss["_rph_hari_ini_delivery_guard_20261110"] = True
                try:
                    try:
                        if source == "checkpoint":
                            outcome = rt._generate_one_quick_rph_v25278(cid, canonical)
                        else:
                            outcome = rt._generate_calendar_row_v25293(cid, canonical, row)
                    except Exception as exc:
                        ss.pop("_free_generation_pending_v25282", None)
                        outcome = {"ok": False, "reason": type(exc).__name__}
                finally:
                    ss.pop("_rph_hari_ini_delivery_guard_20261110", None)
                if outcome.get("ok"):
                    successful_lessons.add(lesson_key)
                results.append((canonical, bool(outcome.get("ok")),
                                str(outcome.get("reason") or "")))
        finally:
            ss.pop("_rph_hari_ini_delivery_guard_20261110", None)
            ss.pop("_daily_suggestions_v25292", None)
        succeeded = sum(bool(ok) for _e, ok, _reason in results)
        lines = ["✨ <b>RPH HARI INI • " + html.escape(current_day) + "</b>", "",
                 "✅ Berjaya: <b>{}/{}</b>".format(succeeded, len(results))]
        for entry, ok, reason in results:
            label = "{} • {} • {}–{}".format(
                entry.get("subject") or "", entry.get("class_name") or "",
                entry.get("start") or "", entry.get("end") or "")
            lines.append(("✓ " if ok else "⚠️ ") + html.escape(label))
            if not ok:
                lines.append("   " + html.escape(reason)[:140])
        lines.extend(["", "Kemajuan PdP hanya disimpan selepas penghantaran RPH berjaya."])
        return rt.send(cid, "\n".join(lines),
                       [[{"text": "⚡ Semak Hari Ini", "callback_data": "todayrph272"}],
                        [{"text": "🏠 Menu Utama", "callback_data": "home"}]])

    def callback(cid, data):
        code = str(data or "")
        if code == "todayrph272":
            return rt._today_rpt_suggestions_v25292(cid)
        if code == "daily292_generate":
            return generate_daily(cid)
        if code == "timetable":
            return timetable(cid)
        # Old inline keyboards are still clickable in Telegram histories.
        # Never allow earlier pre-audit daily generators to bypass this guard.
        if (code.startswith(("todayrph272_", "todaybatch273_",
                             "daily292_", "quicknext275_",
                             "quickpick275_", "quickapply276_"))
                or code == "todaybatch273_run"):
            return rt._today_rpt_suggestions_v25292(cid)
        if code.startswith(("ttupload281_", "tt310_")):
            rt.state.setdefault(cid, {}).pop("waiting", None)
            return timetable(cid, "Fungsi baca/muat naik jadual waktu dimatikan.")
        return old_callback(cid, data)

    # The legacy v25.277 sender records progress immediately after its inner
    # sender returns. Reject a Telegram non-OK response BEFORE that recorder
    # executes, so neither a failed checkpoint nor a trial debit can occur.
    original_inner = getattr(rt, "_send_document_before_v25277", None)
    if not callable(original_inner):
        return False

    def delivery_guard(cid, path, caption=""):
        result = original_inner(cid, path, caption)
        if (rt.state.get(cid, {}).get("_rph_hari_ini_delivery_guard_20261110")
                and "RPH" in str(caption or "").upper()
                and not rt._telegram_delivery_ok_v25279(result)):
            raise RuntimeError("Telegram RPH delivery not confirmed")
        return result

    rt._send_document_before_v25277 = delivery_guard
    if callable(getattr(rt, "_handle_timetable_upload_v25281", None)):
        def no_reader(cid, message):
            rt.state.setdefault(cid, {}).pop("waiting", None)
            return timetable(cid, "Sila isi jadual secara manual.")
        rt._handle_timetable_upload_v25281 = no_reader
    rt.TT_READER_ALLOW_GEMINI = False
    rt._timetable_menu = timetable
    rt.callback = callback
    rt.CIKGULAJU_DAILY_MANUAL_ONLY_20261110 = True
    return True
