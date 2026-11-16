"""Telegram RPH Hari Ini: teacher-entered timetable, verified daily material only.

Never enable timetable photo/PDF reading. Respect the existing RPH / trial
entitlement path and never record a progress checkpoint for a failed delivery.
"""
from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

from web.school_days_2027 import normalize_state


def _english_year(rt, cid, class_name):
    record = rt._profile_class_record(cid, class_name) or {}
    label = record.get("year_label") or record.get("year")
    if label:
        return rt._english_primary_year_number_v2517(label)
    match = re.match(r"^(?:(?:tahun|year|t)\s*)?([1-6])(?=$|[\s/._-]|[A-Za-z])",
                     class_name.strip(), flags=re.IGNORECASE)
    return int(match[1]) if match else None


def _candidate_english_2027(rt, cid, entry, today, year, integrated):
    profile = rt._teacher_profile(cid) or {}
    state = normalize_state(profile.get("state_name"))
    if state is None:
        return None, "english_2027_state_missing"
    sessions = integrated.teaching_week(year, state, today)
    if not sessions:
        return None, "english_2027_no_teaching_session"
    subjects, reason = rt._subject_alias_candidates_v25294(cid, entry)
    subjects = [name for name in subjects
                if rt._norm_subject_v2393(name) in {"english", "bahasainggeris"}]
    if not subjects:
        return None, reason
    for subject in subjects:
        progress = rt._get_rph_progress_v25274(cid, entry["class_name"], subject)
        if progress:
            timestamp = progress.get("last_success_at") or progress.get("updated_at")
            if isinstance(timestamp, str) and timestamp:
                try:
                    saved = datetime.fromisoformat(timestamp)
                except ValueError:
                    saved = None
                if saved is not None:
                    if saved.tzinfo is not None:
                        saved = saved.astimezone(ZoneInfo("Asia/Kuala_Lumpur"))
                    if saved.year < today.year:
                        continue
            row = rt._resolve_next_curriculum_v25276(cid, entry["class_name"], subject, progress)
            number = (rt._checkpoint_no_v25276(row) or 0) if row else 0
            if not 1 <= number <= 160:
                return None, "checkpoint_unresolved"
            year_label = row.get("year_label") or row.get("year")
            if year_label and rt._english_primary_year_number_v2517(year_label) != year:
                return None, "checkpoint_unresolved"
            source = "checkpoint"
            break
    else:
        subject = subjects[0]
        number = sessions[0][0]
        row = rt._resolve_next_english_v25276(f"Tahun {year}", number - 1)
        if row is None or str(row.get("_sequence_no")) != str(number):
            return None, "english_2027_exact_lesson_unavailable"
        source = "calendar_english_2027"

    return {
        **row, "_sequence_no": number, "_resolved_subject_v25294": subject,
        "_english_2027_date": today.isoformat(),
        "_english_2027_pair": integrated.pair_numbers(year, number),
    }, source


def _integrated_plan(rt, cid, entry, row):
    subject = " ".join(str(entry.get("subject") or "").casefold().split())
    if subject not in {"english", "bahasa inggeris", "bi"}:
        return None
    from web import english_integrated_rph_2027 as integrated
    if not integrated.enabled():
        return None
    today = integrated.teaching_date()
    if today.year != 2027 or not integrated.one_hour(entry.get("start"), entry.get("end")):
        return None
    year_label = row.get("year_label") or row.get("year")
    year = (rt._english_primary_year_number_v2517(year_label) if year_label
            else _english_year(rt, cid, entry["class_name"]))
    raw = row.get("_sequence_no") or row.get("lesson_no")
    try:
        number = int(raw)
    except (TypeError, ValueError):
        return None
    pair = integrated.pair_numbers(year, number)
    if pair is None:
        return None
    return today, year, number, pair


def _generate_integrated(rt, cid, entry, row, plan):
    from web import english_integrated_rph_2027 as integrated
    today, year, number, pair = plan
    state = rt.state.setdefault(cid, {})
    snapshot = dict(state)
    try:
        if not rt._apply_verified_next_row_v25277(cid, entry, row):
            return {"ok": False, "reason": "RPH bersepadu belum tersedia"}
        if not rt._credit_gate(cid, state):
            return {"ok": False, "reason": "had FREE/VIP"}
        payload = {
            "class": entry["class_name"], "date": today.isoformat(),
            "time": state.get("rph_time", ""), "students": str(state.get("rph_students") or ""),
        }
        data = integrated.render(year, number, "pdf", payload)
        state["lesson_no"] = state["lesson"] = pair[-1]
        state["textbook_lesson_no"] = pair[-1]
        with TemporaryDirectory() as folder:
            path = Path(folder) / integrated.filename(year, pair, "pdf")
            path.write_bytes(data)
            caption = f"📘 RPH English • Lesson {pair[0]:03d} + {pair[1]:03d}"
            result = rt.send_document(cid, str(path), caption)
        if not rt._telegram_delivery_ok_v25279(result):
            return {"ok": False, "reason": "penghantaran belum disahkan"}
        rt._consume_free_after_success_v25282(cid, "successful_integrated_rph_generation")
        return {"ok": True, "reason": caption}
    finally:
        state.clear()
        state.update(snapshot)


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
    old_candidate = rt._daily_candidate_v25292

    def daily_candidate(cid, entry):
        subject = " ".join(str(entry.get("subject") or "").casefold().split())
        if subject in {"english", "bahasa inggeris", "bi"}:
            from web import english_integrated_rph_2027 as integrated
            if integrated.enabled():
                today = integrated.teaching_date()
                if today.year == 2027 and integrated.one_hour(entry.get("start"), entry.get("end")):
                    year = _english_year(rt, cid, entry["class_name"])
                    if year in range(2, 7):
                        return _candidate_english_2027(rt, cid, entry, today, year, integrated)
        return old_candidate(cid, entry)

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
        seen_slots, successful_lessons, english_classes = set(), set(), set()
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
                if (item.get("row") or {}).get("_english_2027_date") != row.get("_english_2027_date"):
                    results.append((entry, False, "Cadangan telah berubah. Semak RPH Hari Ini semula."))
                    continue
                if row.get("_english_2027_date"):
                    cls_key = " ".join(str(entry.get("class_name") or "").casefold().split())
                    if cls_key in english_classes:
                        results.append((entry, False, "Satu sesi English telah dihantar untuk kelas ini hari ini."))
                        continue
                subj = str(row.get("_resolved_subject_v25294") or entry.get("subject") or "")
                canonical = rt._entry_with_subject_v25294(entry, subj)
                seq = str(row.get("_sequence_no") or row.get("lesson_no") or row.get("sequence_no") or "")
                if not seq:
                    results.append((canonical, False, "Nombor PdP/Lesson belum disahkan"))
                    continue
                ss["_rph_hari_ini_delivery_guard_20261110"] = True
                try:
                    try:
                        integrated_plan = _integrated_plan(rt, cid, canonical, row)
                        lesson_key = (str(canonical.get("class_name") or "").casefold(),
                                      subj.casefold(), str(integrated_plan[-1][0]) if integrated_plan else seq)
                        if lesson_key in successful_lessons:
                            results.append((canonical, False, "PdP/Lesson yang sama sudah dijana"))
                            continue
                        if integrated_plan:
                            outcome = _generate_integrated(rt, cid, canonical, row, integrated_plan)
                        elif source == "checkpoint" and not row.get("_english_2027_date"):
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
                    if row.get("_english_2027_date"):
                        english_classes.add(cls_key)
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
            if reason and (not ok or reason.startswith("📘 RPH English")):
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
    rt._daily_candidate_v25292 = daily_candidate
    previous_summary = getattr(rt, "_next_curriculum_summary_v25276", None)
    if callable(previous_summary):
        def daily_summary(row):
            pair = (row or {}).get("_english_2027_pair")
            if pair:
                return f"Lesson {pair[0]:03d} + {pair[1]:03d} • Satu RPH"
            return previous_summary(row)
        rt._next_curriculum_summary_v25276 = daily_summary
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
