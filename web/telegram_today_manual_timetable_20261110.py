"""Telegram RPH Hari Ini: manual timetable only, reviewed-source slot generation.

This adapter replaces the paused legacy daily buttons without enabling the old
batch handler. Timetable records are read from existing teacher_profiles /
class_profiles. The old image/PDF AI reader is disabled at its menu, callback
and upload handler; manual entry / delete and the underlying RPH engine remain.
"""
from __future__ import annotations

import html
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

PREFIX = "tm26:"
MAX_SLOTS = 18
VALID_SOURCES = frozenset(("checkpoint", "calendar_verified_rpt", "calendar_verified_sow"))
VALID_RESOLVERS = frozenset((
    "verified_rpt_entries",
    "english_y1_y2_verified_rows",
    "english_y3_y6_verified_sow",
))
_UPLOAD_KEYS = (
    "waiting", "_tt286_raw_draft", "_tt286_edit_old",
    "_tt_upload_draft_v25281", "_tt_upload_unmatched_v25281",
)
_ACTIVE_LOCK = threading.Lock()
_ACTIVE_USERS = set()


def _date():
    return datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date().isoformat()


def _esc(value):
    return html.escape(str(value or ""), quote=True)


def _btn(label, action):
    return {"text": label, "callback_data": PREFIX + action}


def _back_buttons():
    return [[_btn("⚡ RPH Hari Ini", "home")],
            [{"text": "🏠 Menu Utama", "callback_data": "home"}]]


def _clean_upload_drafts(runtime, cid):
    state = runtime.state.setdefault(cid, {})
    if str(state.get("waiting") or "") == "timetable_upload_v25281":
        state.pop("waiting", None)
    for key in _UPLOAD_KEYS[1:]:
        state.pop(key, None)


def _manual_timetable_menu(runtime, cid, note=""):
    _clean_upload_drafts(runtime, cid)
    rows = runtime._timetable_entries(cid)
    lines = ["📅 <b>JADUAL WAKTU SAYA</b>", "",
             "✏️ <b>Masukkan jadual secara manual.</b> "
             "Tiada fungsi baca gambar/PDF jadual waktu.", ""]
    if note:
        lines.extend([_esc(note), ""])
    if not rows:
        lines.append("Belum ada jadual. Tambah kelas di Profil, kemudian isi hari, "
                     "waktu mula/tamat dan subjek.")
    else:
        day = None
        for entry in rows[:60]:
            if entry.get("day") != day:
                day = entry.get("day")
                lines.append("<b>" + _esc(day) + "</b>")
            lines.append("• " + _esc(entry.get("start")) + "–" +
                         _esc(entry.get("end")) + " | " +
                         _esc(entry.get("class_name")) + " | " +
                         _esc(entry.get("subject")))
        if len(rows) > 60:
            lines.append("• … baki slot masih disimpan")
    keyboard = [
        [{"text": "➕ Isi / Tambah Waktu Manual", "callback_data": "tt_add"}],
        [{"text": "⚡ RPH Hari Ini", "callback_data": "todayrph272"}],
    ]
    if rows:
        keyboard.extend([
            [{"text": "🗑️ Padam Waktu", "callback_data": "tt_delete"}],
            [{"text": "🧹 Kosongkan Jadual (Sahkan)", "callback_data": "tt311_clear_ask"}],
        ])
    keyboard.extend([
        [{"text": "🏫 Urus Kelas", "callback_data": "profclass_manage"}],
        [{"text": "👤 Profil Saya", "callback_data": "account"}],
        [{"text": "🏠 Menu Utama", "callback_data": "home"}],
    ])
    return runtime.send(cid, "\n".join(lines)[:3900], keyboard)


def _upload_disabled(runtime, cid, *args, **kwargs):
    _clean_upload_drafts(runtime, cid)
    return runtime.send(
        cid,
        "✏️ <b>Jadual waktu hanya diisi secara manual.</b>\n\n"
        "Pilih kelas, hari, waktu mula/tamat dan subjek. "
        "Rekod yang sudah disimpan tidak diubah.",
        [[{"text": "➕ Isi Jadual Manual", "callback_data": "tt_add"}],
         [{"text": "📅 Lihat Jadual", "callback_data": "timetable"}],
         [{"text": "🏠 Menu Utama", "callback_data": "home"}]],
    )


def _is_reader_button(callback_data):
    data = str(callback_data or "")
    # Previously sent Telegram inline buttons remain clickable after deployment.
    # Reader-specific confirmation/edit buttons must not commit old OCR drafts.
    return data.startswith(("ttupload281_", "tt286_"))


def _slot_key(day_iso, entry):
    return "|".join((day_iso, str(entry.get("day") or ""),
                     str(entry.get("start") or ""), str(entry.get("end") or ""),
                     str(entry.get("class_name") or ""), str(entry.get("subject") or "")))


def _day_rows(runtime, cid):
    day, rows = runtime._today_rows_v25272(cid)
    # Do not ever trust an index from an old keyboard, and avoid duplicated slots.
    seen = set()
    output = []
    for index, raw in rows:
        entry = dict(raw)
        key = _slot_key(_date(), entry)
        if key in seen:
            continue
        seen.add(key)
        output.append((index, entry))
    return day, output[:MAX_SLOTS]


def _candidate(runtime, cid, entry):
    try:
        row, source = runtime._daily_candidate_v25292(cid, entry)
        if not isinstance(row, dict) or source not in VALID_SOURCES:
            return None, str(source or "Padanan tidak tersedia")
        resolver = str(row.get("_resolver") or "")
        if resolver not in VALID_RESOLVERS:
            return None, "Sumber PdP/Lesson belum disahkan"
        canonical = str(row.get("_resolved_subject_v25294") or entry.get("subject") or "")
        if not canonical.strip() or not str(entry.get("class_name") or "").strip():
            return None, "Subjek atau kelas tidak lengkap"
        chosen = runtime._entry_with_subject_v25294(entry, canonical)
        no = row.get("_sequence_no") or row.get("lesson_no") or row.get("sequence_no")
        if not str(no or "").strip() or not str(chosen.get("start") or "").strip() or not str(chosen.get("end") or "").strip():
            return None, "Nombor Lesson/PdP atau masa tidak lengkap"
        summary = str(runtime._next_curriculum_summary_v25276(row) or "").strip()
        if not summary:
            return None, "Ringkasan PdP tidak tersedia"
        fingerprint = (source, resolver, canonical, str(no),
                       str(row.get("id") or row.get("rpt_entry_id") or ""),
                       summary)
        return {"entry": chosen, "row": row, "source": source,
                "summary": summary, "fingerprint": fingerprint}, "ready"
    except Exception as exc:
        print("TELEGRAM TODAY SOURCE LOOKUP ERROR:", type(exc).__name__, flush=True)
        return None, "Sumber kurikulum belum tersedia"


def _state(runtime, cid):
    return runtime.state.setdefault(cid, {})


def _completed(runtime, cid):
    root = _state(runtime, cid)
    completed = root.get("_today_manual_completed_20261110")
    if not isinstance(completed, dict):
        completed = {}
        root["_today_manual_completed_20261110"] = completed
    # Bound in-memory history; this is NOT a substitute for permanent RPH progress.
    if len(completed) > 70:
        today = _date()
        for k in list(completed):
            if not k.startswith(today + "|"):
                completed.pop(k, None)
    return completed


def _home(runtime, cid):
    _clean_upload_drafts(runtime, cid)
    day, rows = _day_rows(runtime, cid)
    today = _date()
    if not rows:
        return runtime.send(
            cid, "⚡ <b>RPH HARI INI • " + _esc(day.upper()) + "</b>\n\n"
                 "Jadual hari ini kosong. Isi jadual waktu secara manual "
                 "di Profil terlebih dahulu. Tiada RPH dijana atau kuota ditolak.",
            [[{"text": "➕ Isi Jadual Manual", "callback_data": "tt_add"}],
             [{"text": "📅 Jadual Saya", "callback_data": "timetable"}],
             [{"text": "🏠 Menu Utama", "callback_data": "home"}]],
        )
    lines = ["⚡ <b>RPH HARI INI • " + _esc(day.upper()) + "</b>",
             "📅 " + _esc(today), "",
             "Slot mengajar daripada <b>jadual yang cikgu isi sendiri</b>.",
             "Sila semak Lesson/PdP cadangan sebelum menjana RPH.", ""]
    keys = []
    rows_button = []
    done = _completed(runtime, cid)
    ready_count = 0
    for index, entry in rows:
        key = _slot_key(today, entry)
        slot = (_esc(entry.get("start")) + "–" + _esc(entry.get("end")) +
                " • " + _esc(entry.get("subject")) + " • " + _esc(entry.get("class_name")))
        if key in done:
            lines.append("✅ " + slot + " — RPH telah dihantar")
            continue
        candidate, reason = _candidate(runtime, cid, entry)
        if candidate is None:
            lines.append("⚠️ " + slot + " — " + _esc(reason)[:120])
            continue
        ready_count += 1
        keys.append(key)
        lines.append("📝 " + slot + "\n    ↳ " + _esc(candidate["summary"])[:135])
        rows_button.append([_btn(("📝 Semak " + str(index + 1) + " • " +
                                  str(entry.get("subject") or ""))[:60],
                                 "slot:" + str(index))])
    buttons = rows_button
    if ready_count:
        buttons.append([_btn("✨ Semak & Jana Semua Slot Tersedia", "all")])
    buttons += [
        [{"text": "✏️ Isi / Ubah Jadual Manual", "callback_data": "timetable"}],
        [{"text": "📚 Pilih Lesson/PdP Sendiri", "callback_data": "quick"}],
        [{"text": "🏠 Menu Utama", "callback_data": "home"}],
    ]
    if not ready_count:
        lines.extend(["", "Belum ada padanan kurikulum yang boleh dijana secara "
                      "automatik. Pilih Lesson/PdP sendiri; jangan gunakan RPH generik."])
    return runtime.send(cid, "\n".join(lines)[:3900], buttons)


def _find_slot(runtime, cid, selected):
    try:
        index = int(selected)
    except (ValueError, TypeError):
        raise ValueError("Indeks slot tidak sah")
    day, rows = _day_rows(runtime, cid)
    for actual_index, entry in rows:
        if actual_index == index:
            return entry
    raise ValueError("Slot sudah berubah atau bukan jadual hari ini")


def _preview(runtime, cid, selected):
    entry = _find_slot(runtime, cid, selected)
    key = _slot_key(_date(), entry)
    if key in _completed(runtime, cid):
        return runtime.send(cid, "✅ RPH slot ini sudah dihantar hari ini.", _back_buttons())
    candidate, reason = _candidate(runtime, cid, entry)
    if candidate is None:
        return runtime.send(
            cid, "⚠️ Padanan kurikulum untuk slot ini belum boleh disahkan: " +
                 _esc(reason) + ". Sila pilih Lesson/PdP secara manual.",
            [[{"text": "📚 Sediakan RPH Manual", "callback_data": "quick"}]]
            + _back_buttons())
    _state(runtime, cid)["_today_manual_preview_20261110"] = {
        "date": _date(), "key": key, "fingerprint": candidate["fingerprint"]
    }
    source_label = ("PdP/Lesson seterusnya daripada rekod kelas" if
                    candidate["source"] == "checkpoint" else
                    "Cadangan RPT/SOW mengikut tarikh — sila semak")
    return runtime.send(
        cid, "📝 <b>SEMAK RPH HARI INI</b>\n\n"
             "Kelas: <b>" + _esc(entry.get("class_name")) + "</b>\n"
             "Subjek: <b>" + _esc(candidate["entry"].get("subject")) + "</b>\n"
             "Tarikh: <b>" + _esc(_date()) + "</b>\n"
             "Masa: <b>" + _esc(entry.get("start")) + "–" + _esc(entry.get("end")) + "</b>\n"
             "Lesson/PdP: <b>" + _esc(candidate["summary"]) + "</b>\n\n"
             "📚 " + _esc(source_label) + ".\n"
             "Kuota hanya ditolak setelah RPH berjaya dijana dan dihantar.",
        [[_btn("✅ Sahkan & Jana RPH Slot Ini", "make:" + str(selected))],
         [{"text": "📚 Pilih Lesson/PdP Sendiri", "callback_data": "quick"}]]
        + _back_buttons(),
    )


def _enter_running(cid):
    with _ACTIVE_LOCK:
        if cid in _ACTIVE_USERS:
            return False
        _ACTIVE_USERS.add(cid)
        return True


def _exit_running(cid):
    with _ACTIVE_LOCK:
        _ACTIVE_USERS.discard(cid)


def _generate_slot(runtime, cid, entry, candidate):
    """Delegates PDF generation and one credit to the EXISTING engine.

    The native helper gates access and only considers Telegram-acknowledged
    delivery successful. Do not implement a second billing flow here.
    """
    date_iso = _date()
    key = _slot_key(date_iso, entry)
    if key in _completed(runtime, cid):
        return True, "already_sent"
    snapshot = dict(_state(runtime, cid))
    try:
        resolved_entry = candidate["entry"]
        if candidate["source"] == "checkpoint":
            result = runtime._generate_one_quick_rph_v25278(cid, resolved_entry)
        else:
            result = runtime._generate_calendar_row_v25293(
                cid, resolved_entry, candidate["row"])
        if not isinstance(result, dict) or result.get("ok") is not True:
            return False, str((result or {}).get("reason") or "Janaan tidak disahkan")[:150]
        # Mark only after native result confirms successful Telegram delivery.
        _completed(runtime, cid)[key] = candidate["fingerprint"]
        return True, "success"
    finally:
        # The legacy calendar adapter fills mutable RPH context fields; restore
        # the teacher's previous navigation without undoing durable progress.
        previous_done = _completed(runtime, cid)
        runtime.state[cid] = snapshot
        runtime.state[cid]["_today_manual_completed_20261110"] = previous_done


def _make(runtime, cid, selected):
    if not _enter_running(cid):
        return runtime.send(cid, "⏳ Janaan slot sedang diproses.", _back_buttons())
    try:
        entry = _find_slot(runtime, cid, selected)
        preview = _state(runtime, cid).get("_today_manual_preview_20261110") or {}
        key = _slot_key(_date(), entry)
        if key in _completed(runtime, cid):
            return runtime.send(cid, "✅ RPH slot ini sudah dihantar hari ini.", _back_buttons())
        if preview.get("date") != _date() or preview.get("key") != key:
            return runtime.send(cid, "⚠️ Sahkan semula slot hari ini sebelum jana.", _back_buttons())
        candidate, reason = _candidate(runtime, cid, entry)
        if candidate is None or candidate["fingerprint"] != preview.get("fingerprint"):
            return runtime.send(cid, "⚠️ PdP/Lesson telah berubah. Semak semula dahulu.",
                                [[_btn("🔄 Semak Slot Semula", "slot:" + str(selected))]]
                                + _back_buttons())
        ok, status = _generate_slot(runtime, cid, entry, candidate)
        if ok:
            return runtime.send(
                cid, "✅ <b>RPH Hari Ini berjaya dihantar.</b>\n\n" +
                     _esc(entry.get("subject")) + " • " + _esc(entry.get("class_name")) +
                     " • " + _esc(candidate["summary"]),
                _back_buttons())
        return runtime.send(
            cid, "⚠️ RPH belum berjaya: " + _esc(status) +
                 "\nTiada janaan dianggap berjaya jika penghantaran gagal.",
            _back_buttons())
    except Exception as exc:
        print("TELEGRAM TODAY SLOT ERROR:", type(exc).__name__, flush=True)
        return runtime.send(cid, "⚠️ Slot tidak dapat diproses. "
                            "Sila buka semula RPH Hari Ini.", _back_buttons())
    finally:
        _exit_running(cid)


def _plan_all(runtime, cid):
    day, rows = _day_rows(runtime, cid)
    planned = []
    lines = ["✨ <b>SEMAK SEBELUM JANA SEMUA</b>", "",
             "Semak cadangan PdP/Lesson bagi setiap slot. "
             "Satu RPH berjaya = satu janaan (kecuali akses tanpa had).", ""]
    seen_subjects = set()
    held = 0
    for index, entry in rows:
        key = _slot_key(_date(), entry)
        if key in _completed(runtime, cid):
            continue
        # One lesson per class+subject per batch; the next occurrence needs a
        # fresh checkpoint after the preceding RPH is delivered.
        subject_key = (str(entry.get("class_name") or "").casefold(),
                       str(entry.get("subject") or "").casefold())
        if subject_key in seen_subjects:
            held += 1
            continue
        seen_subjects.add(subject_key)
        candidate, reason = _candidate(runtime, cid, entry)
        if candidate is None:
            held += 1
            continue
        planned.append((index, key, candidate["fingerprint"]))
        lines.append("• " + _esc(entry.get("start")) + " " +
                     _esc(entry.get("class_name")) + " • " +
                     _esc(candidate["entry"].get("subject")) + "\n  ↳ " +
                     _esc(candidate["summary"])[:140])
    if not planned:
        return runtime.send(cid, "⚠️ Tiada padanan yang sedia untuk janaan. "
                            "Cikgu boleh memilih Lesson/PdP secara manual.",
                            [[{"text": "📚 Sediakan Manual", "callback_data": "quick"}]]
                            + _back_buttons())
    _state(runtime, cid)["_today_manual_batch_20261110"] = {
        "date": _date(), "planned": tuple(planned)
    }
    if held:
        lines += ["", "⚠️ " + str(held) +
                  " slot lain perlu dipilih secara manual atau disemak selepas "
                  "RPH sebelumnya berjaya dihantar."]
    lines.extend(["", "Janaan hanya dimulakan selepas cikgu tekan SAHKAN."])
    return runtime.send(cid, "\n".join(lines)[:3850],
                        [[_btn("✅ SAHKAN • Jana " + str(len(planned)) + " RPH", "runall")]]
                        + _back_buttons())


def _run_all(runtime, cid):
    if not _enter_running(cid):
        return runtime.send(cid, "⏳ Janaan RPH Hari Ini sedang berjalan.", _back_buttons())
    try:
        batch = _state(runtime, cid).pop("_today_manual_batch_20261110", {})
        if batch.get("date") != _date() or not batch.get("planned"):
            return runtime.send(cid, "⚠️ Semak semula jadual dan Lesson/PdP sebelum jana.",
                                _back_buttons())
        # One-time confirmation; old inline keyboard cannot repeat the same batch.
        planned = list(batch["planned"])[:MAX_SLOTS]
        successes, failures = [], []
        for index, expected_key, expected_fingerprint in planned:
            try:
                entry = _find_slot(runtime, cid, index)
                key = _slot_key(_date(), entry)
                if key != expected_key:
                    raise ValueError("Slot telah berubah")
                if key in _completed(runtime, cid):
                    continue
                candidate, reason = _candidate(runtime, cid, entry)
                if candidate is None or candidate["fingerprint"] != expected_fingerprint:
                    raise ValueError("PdP/Lesson berubah — semak semula")
                ok, result = _generate_slot(runtime, cid, entry, candidate)
                (successes if ok else failures).append(
                    _esc(entry.get("subject")) + " • " +
                    _esc(entry.get("class_name")) +
                    ("" if ok else " — " + _esc(result)))
            except Exception as exc:
                failures.append("Slot " + str(index + 1) +
                                " — " + _esc(str(exc)[:100]))
        lines = ["✅ <b>HASIL RPH HARI INI</b>", "",
                 "Berjaya: <b>" + str(len(successes)) + "</b> | "
                 "Belum berjaya: <b>" + str(len(failures)) + "</b>"]
        if successes:
            lines += ["", "<b>RPH dihantar:</b>"] + ["• " + x for x in successes]
        if failures:
            lines += ["", "<b>Perlu semakan:</b>"] + ["• " + x for x in failures]
        lines.extend(["", "Slot gagal tidak dianggap sebagai janaan berjaya. "
                      "Pilih manual untuk PdP/Lesson yang belum dipadankan."])
        return runtime.send(cid, "\n".join(lines)[:3850], _back_buttons())
    finally:
        _exit_running(cid)


def _dispatch(runtime, cid, code):
    try:
        if code == "home":
            return _home(runtime, cid)
        if code.startswith("slot:"):
            return _preview(runtime, cid, code.split(":", 1)[1])
        if code.startswith("make:"):
            return _make(runtime, cid, code.split(":", 1)[1])
        if code == "all":
            return _plan_all(runtime, cid)
        if code == "runall":
            return _run_all(runtime, cid)
    except Exception as exc:
        print("TELEGRAM TODAY MENU ERROR:", type(exc).__name__, flush=True)
    return runtime.send(cid, "⚠️ Pilihan telah berubah. Buka RPH Hari Ini semula.",
                        _back_buttons())


def install(runtime):
    """Install after existing timetable, credit, special-activity and menu adapters."""
    if getattr(runtime, "CIKGULAJU_MANUAL_TODAY_RPH_ACTIVE", False):
        return True
    names = (
        "send", "menu", "callback", "_timetable_menu", "_timetable_entries",
        "_today_rows_v25272", "_daily_candidate_v25292",
        "_entry_with_subject_v25294", "_next_curriculum_summary_v25276",
        "_generate_one_quick_rph_v25278", "_generate_calendar_row_v25293",
        "_tt_upload_menu_v25281", "_handle_timetable_upload_v25281",
    )
    if not all(callable(getattr(runtime, n, None)) for n in names):
        return False
    if not isinstance(getattr(runtime, "state", None), dict):
        return False
    old_callback, old_menu = runtime.callback, runtime.menu

    def callback(cid, data):
        value = str(data or "")
        if _is_reader_button(value):
            return _upload_disabled(runtime, cid)
        if value in ("todayrph272",) or value.startswith("todayrph272_"):
            return _home(runtime, cid)
        # Old paused batch links must never reach outdated automatic generators.
        if value in ("daily292_generate", "todaybatch273_run") or value.startswith(
                ("quicknext275_", "quickpick275_", "quickapply276_")):
            return _home(runtime, cid)
        if value.startswith(PREFIX):
            return _dispatch(runtime, cid, value[len(PREFIX):])
        return old_callback(cid, data)

    def menu(cid, show_persistent=False):
        result = old_menu(cid, show_persistent=show_persistent)
        # The existing Special Activity menu can show today's shortcut in its
        # supplementary message. If that optional integration failed to load,
        # retain an independent visible entry for RPH Hari Ini.
        if not getattr(runtime, "CIKGULAJU_TELEGRAM_SPECIAL_RPH_MENU_ACTIVE", False):
            try:
                runtime.send(cid, "⚡ <b>RPH Hari Ini</b> — Jadual diisi manual",
                             [[_btn("⚡ Buka RPH Hari Ini", "home")]])
            except Exception as exc:
                print("TELEGRAM TODAY MENU FALLBACK:", type(exc).__name__, flush=True)
        return result

    runtime._timetable_menu = lambda cid, note="": _manual_timetable_menu(runtime, cid, note)
    runtime._tt_upload_menu_v25281 = lambda cid: _upload_disabled(runtime, cid)
    runtime._handle_timetable_upload_v25281 = (
        lambda cid, message: _upload_disabled(runtime, cid))
    runtime.callback = callback
    runtime.menu = menu
    runtime.CIKGULAJU_MANUAL_TODAY_RPH_ACTIVE = True
    return True
