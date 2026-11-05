"""Additive Telegram school-name edit and shared profile display.

The existing Telegram profile/class/timetable handlers already use the same
teacher_profiles.class_profiles record now used by Web. This adapter only adds
the missing school field to the Telegram screen and its native editor.

It does not alter Telegram lesson, payment, subscription, credit, RPH or
timetable handlers. Only private, already-initiated school edits are handled.
"""
from datetime import datetime, timezone
import html
import time
from urllib.parse import urlencode


def install(runtime):
    if getattr(runtime, "_shared_school_profile_installed", False):
        return True
    needed = (
        "app", "state", "callback", "send", "_teacher_profile", "_sb_request",
        "_profile_edit_menu", "_profile_class_records", "_clean_profile_page_v25296",
        "_profile_access_label_v25296", "_profile_daily_readiness_v25296",
    )
    if not all(hasattr(runtime, name) for name in needed):
        return False
    if not hasattr(runtime.app, "before_request"):
        return False

    original_callback = runtime.callback
    original_profile_page = runtime._clean_profile_page_v25296
    original_edit_menu = runtime._profile_edit_menu

    def _identifier(value):
        try:
            number = int(value)
            return number if number > 0 else None
        except (TypeError, ValueError):
            return None

    def _send_account_page(cid):
        p = runtime._teacher_profile(cid)
        if not p:
            return original_profile_page(cid)
        name = html.escape(str(p.get("display_name") or "—"))
        school = html.escape(str(p.get("school_name") or "Belum diisi"))
        state = html.escape(str(p.get("state_name") or "—"))
        access = html.escape(str(runtime._profile_access_label_v25296(cid)))
        readiness = runtime._profile_daily_readiness_v25296(cid)
        return runtime.send(
            cid,
            "👤 <b>PROFIL SAYA</b>\n\n"
            "<b>Maklumat Cikgu</b>\n"
            f"Nama: <b>{name}</b>\n"
            f"Sekolah: <b>{school}</b>\n"
            f"Negeri: <b>{state}</b>\n\n"
            "<b>Akses CikguLaju</b>\n"
            f"{access}\n\n"
            "<b>Persediaan RPH Hari Ini</b>\n"
            f"{readiness}",
            [
                [{"text": "📅 LIHAT / URUS JADUAL", "callback_data": "timetable"}],
                [{"text": "✏️ KEMAS KINI PROFIL", "callback_data": "profile_edit"}],
                [{"text": "💬 KOMEN & CADANGAN", "callback_data": "beta_feedback"}],
                [{"text": "🏠 MENU UTAMA", "callback_data": "home"}],
            ],
        )

    def _send_edit_menu(cid):
        p = runtime._teacher_profile(cid)
        if not p:
            return original_edit_menu(cid)
        rows = runtime._profile_class_records(cid)
        classes = ", ".join(
            f"{r['name']} ({r['students']} murid)" if r.get("students")
            else r["name"] for r in rows
        ) or "—"
        name = html.escape(str(p.get("display_name") or "—"))
        school = html.escape(str(p.get("school_name") or "Belum diisi"))
        state = html.escape(str(p.get("state_name") or "—"))
        return runtime.send(
            cid,
            "👤 <b>Kemaskini Profil</b>\n\n"
            f"Nama/Panggilan: <b>{name}</b>\n"
            f"Nama sekolah: <b>{school}</b>\n"
            f"Negeri: <b>{state}</b>\n"
            f"Kelas: <b>{html.escape(classes)}</b>\n\n"
            "Pilih bahagian yang mahu diubah.",
            [
                [{"text": "✏️ Nama/Panggilan", "callback_data": "profedit_name"}],
                [{"text": "🏫 Nama Sekolah", "callback_data": "profedit_school"}],
                [{"text": "📍 Negeri", "callback_data": "profedit_state"}],
                [{"text": "🏫 Urus Kelas", "callback_data": "profclass_manage"}],
                [{"text": "⬅️ Akaun & Profil", "callback_data": "my_account"}],
                [{"text": "🏠 Menu Utama", "callback_data": "home"}],
            ],
        )

    def _clear_school_waiting(cid):
        ss = runtime.state.get(cid) or {}
        for field in ("waiting", "_school_shared_version", "_school_shared_started"):
            ss.pop(field, None)

    def _callback_school(cid, data):
        value = str(data or "")
        if value != "profedit_school":
            if (runtime.state.get(cid) or {}).get("waiting") == "profile_school_shared":
                _clear_school_waiting(cid)
            return original_callback(cid, data)
        uid = _identifier(cid)
        if uid is None:
            return runtime.send(cid, "⚠️ Buka profil melalui sembang peribadi bot.")
        profile = runtime._teacher_profile(uid)
        if not profile or not profile.get("updated_at"):
            return runtime.send(
                uid, "⚠️ Profil belum tersedia. Sediakan profil terlebih dahulu.")
        ss = runtime.state.setdefault(uid, {})
        ss["waiting"] = "profile_school_shared"
        ss["_school_shared_version"] = str(profile["updated_at"])
        ss["_school_shared_started"] = time.time()
        return runtime.send(
            uid,
            "🏫 <b>Nama Sekolah</b>\n\n"
            "Taip nama sekolah yang betul, contohnya <b>SK Taman Maju</b>.\n"
            "Taip <code>-</code> jika mahu kosongkan medan ini.\n"
            "Tekan Batal jika tidak mahu mengubahnya.",
            [[{"text": "❌ Batal", "callback_data": "profedit_menu"}]],
        )

    recent_school_updates = set()
    recent_school_order = []

    def _handled_school_update(update_id):
        if update_id in recent_school_updates:
            return
        recent_school_updates.add(update_id)
        recent_school_order.append(update_id)
        if len(recent_school_order) > 250:
            recent_school_updates.discard(recent_school_order.pop(0))

    def _school_message():
        from flask import request, jsonify

        if request.endpoint != "webhook" or request.method != "POST":
            return None
        if not request.is_json or request.content_length is None or request.content_length > 16384:
            return None
        update = request.get_json(silent=True)
        if not isinstance(update, dict) or type(update.get("update_id")) is not int:
            return None
        update_id = update["update_id"]
        if update_id in recent_school_updates:
            return jsonify({"ok": True, "duplicate": True})
        message = update.get("message")
        if not isinstance(message, dict):
            return None
        chat, sender = message.get("chat") or {}, message.get("from") or {}
        uid = _identifier(chat.get("id"))
        if (not uid or chat.get("type") != "private" or
                _identifier(sender.get("id")) != uid):
            return None
        ss = runtime.state.get(uid) or {}
        if ss.get("waiting") != "profile_school_shared":
            return None
        _handled_school_update(update_id)
        value = message.get("text")
        if not isinstance(value, str):
            return None
        if value.strip().startswith("/") and value.strip().lower() not in ("/batal", "/cancel"):
            return None
        if value.strip().lower() in ("/batal", "/cancel"):
            _clear_school_waiting(uid)
            runtime.send(uid, "Pengemaskinian sekolah dibatalkan.")
            return jsonify({"ok": True})
        school = value.strip()
        if (len(school) > 160 or any(ord(c) < 32 for c in school)
                or not school or
                time.time() - float(ss.get("_school_shared_started") or 0) > 600):
            runtime.send(uid, "⚠️ Nama sekolah tidak sah atau sesi tamat. Pilih Nama Sekolah semula.")
            return jsonify({"ok": True})
        if school == "-":
            school = ""
        version = ss.get("_school_shared_version") or ""
        if not version:
            return jsonify({"ok": True})
        filters = urlencode({
            "telegram_user_id": "eq." + str(uid),
            "updated_at": "eq." + version,
            "select": "telegram_user_id,updated_at",
        })
        payload = {
            "school_name": school,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            saved = runtime._sb_request(
                "PATCH", "teacher_profiles?" + filters,
                json=payload, prefer="return=representation",
            )
        except Exception:
            runtime.send(uid, "⚠️ Maklumat belum dapat disimpan. Sila cuba lagi.")
            return jsonify({"ok": True})
        if not isinstance(saved, list) or len(saved) != 1 or _identifier(saved[0].get("telegram_user_id")) != uid:
            _clear_school_waiting(uid)
            runtime.send(uid, "⚠️ Profil telah berubah di tempat lain. Buka semula Profil sebelum mengemas kini.")
            return jsonify({"ok": True})
        _clear_school_waiting(uid)
        runtime.send(uid, "✅ Nama sekolah telah dikemas kini.")
        _send_account_page(uid)
        return jsonify({"ok": True})

    runtime._clean_profile_page_v25296 = _send_account_page
    runtime._profile_edit_menu = _send_edit_menu
    runtime.callback = _callback_school
    runtime.app.before_request(_school_message)
    runtime._shared_school_profile_installed = True
    return True
