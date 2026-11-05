"""Admin-confirmed, one-time Telegram announcement for the CikguLaju Web launch.

No sending at import, install, panel opening, or preview.
Sending begins *only* after an authorized, fresh Telegram confirmation.
Campaign + recipients are snapshotted atomically in Supabase (private RLS).
Each recipient is claimed exactly once, even across workers/restarts.
Uncertain 'sending' rows are never automatically resent after a crash.
"""
from __future__ import annotations

import hashlib
import re
import secrets
import threading
import time
from datetime import datetime, timezone

import requests

CAMPAIGN = "web_launch_20261106"
WEB_URL = "https://cikgulaju-web.onrender.com/"
BUTTON = {"text": "📢 Hebahan Pengguna", "callback_data": "admin_web_broadcast|preview"}
TTL_SECONDS = 600
PAGE_SIZE = 500
MAX_USERS = 20000
DELAY_SECONDS = 0.20
_SEND_LOCK = threading.Lock()

ANNOUNCEMENT = (
    "🌐 <b>CIKGULAJU KINI BOLEH DIGUNAKAN MELALUI WEB!</b>\n\n"
    "Alhamdulillah, kini cikgu boleh menggunakan CikguLaju melalui "
    "telefon atau komputer dengan paparan yang lebih mudah.\n\n"
    "✅ Sediakan RPH Word/PDF bagi Lesson/PdP yang tersedia\n"
    "✅ Muat turun RPT 2027 yang tersedia\n"
    "✅ Simpan profil guru, sekolah dan kelas\n"
    "✅ Muat naik logo sekolah untuk muka depan RPT\n\n"
    "<b>Pengguna sedia ada tidak perlu mendaftar semula.</b> "
    "Log masuk menggunakan akaun Telegram CikguLaju yang sama.\n\n"
    "🏆 Rakan Pembangun yang sudah aktif tidak perlu membayar lagi. "
    "Akses sedia ada kekal.\n\n"
    "🔗 <b>WEB CIKGULAJU</b>\n" + WEB_URL + "\n\n"
    "Terima kasih atas sokongan cikgu. Penambahbaikan sedang diteruskan."
)
MESSAGE_SHA256 = hashlib.sha256(ANNOUNCEMENT.encode("utf-8")).hexdigest()
WEB_KEYBOARD = {"inline_keyboard": [[{
    "text": "🌐 Buka Web CikguLaju", "url": WEB_URL,
}]]}
_CONFIRM = re.compile(r"^admin_web_broadcast\|confirm\|([a-f0-9]{16})$")
_ACTIONS = frozenset((
    "admin_web_broadcast|preview",
    "admin_web_broadcast|status",
    "admin_web_broadcast|resume",
    "admin_web_broadcast|cancel",
))


def _ids(sb):
    """Read ONLY registered durable Telegram users; never local/stale SQLite."""
    ids = set()
    offset = 0
    while True:
        rows = sb(
            "GET", "cikgulaju_users?select=telegram_user_id"
                   f"&order=telegram_user_id.asc&limit={PAGE_SIZE}&offset={offset}"
        )
        if not isinstance(rows, list) or len(rows) > PAGE_SIZE:
            raise RuntimeError("Supabase registered-user directory unavailable")
        for row in rows:
            if not isinstance(row, dict) or type(row.get("telegram_user_id")) is not int:
                raise RuntimeError("Invalid Telegram user record")
            uid = row["telegram_user_id"]
            if uid <= 0:
                raise RuntimeError("Invalid Telegram user ID")
            ids.add(uid)
        offset += len(rows)
        if offset > MAX_USERS:
            raise RuntimeError("Recipient count exceeds guarded limit")
        if len(rows) < PAGE_SIZE:
            break
    return len(ids)


def _campaign(sb):
    rows = sb(
        "GET", "cikgulaju_broadcast_campaigns?select="
               "campaign_id,recipient_count,confirmed_by,confirmed_at"
               f"&campaign_id=eq.{CAMPAIGN}&limit=2",
    )
    if not isinstance(rows, list) or len(rows) > 1:
        raise RuntimeError("Campaign audit record unavailable")
    return rows[0] if rows else None


def _status(sb):
    entry = _campaign(sb)
    if entry is None:
        return None
    tally = {key: 0 for key in ("queued", "sending", "sent", "failed")}
    offset = 0
    while True:
        rows = sb(
            "GET", "cikgulaju_broadcast_deliveries?select=status"
                   f"&campaign_id=eq.{CAMPAIGN}"
                   f"&order=telegram_user_id.asc&limit={PAGE_SIZE}&offset={offset}"
        )
        if not isinstance(rows, list) or len(rows) > PAGE_SIZE:
            raise RuntimeError("Broadcast audit is unavailable")
        for row in rows:
            if not isinstance(row, dict) or row.get("status") not in tally:
                raise RuntimeError("Unexpected broadcast status")
            tally[row["status"]] += 1
        offset += len(rows)
        if offset > MAX_USERS:
            raise RuntimeError("Broadcast exceeds guarded limit")
        if len(rows) < PAGE_SIZE:
            break
    total = int(entry["recipient_count"])
    if total != sum(tally.values()):
        raise RuntimeError("Campaign and recipient counts do not match")
    return dict(tally, total=total)


def _next_recipient(sb):
    rows = sb("POST", "rpc/cikgulaju_broadcast_claim",
              json={"p_campaign": CAMPAIGN})
    if not isinstance(rows, list) or len(rows) > 1:
        raise RuntimeError("Atomic recipient claim unavailable")
    if not rows:
        return None
    uid = rows[0].get("telegram_user_id") if isinstance(rows[0], dict) else None
    if type(uid) is not int or uid <= 0:
        raise RuntimeError("Invalid claimed user ID")
    return uid


def _record(sb, uid, status, category=None):
    if status not in ("sent", "failed"):
        raise ValueError("Unexpected delivery decision")
    if category is not None and category not in (
        "blocked", "chat_missing", "rate_limited", "telegram_error",
        "transport_error", "unconfirmed"
    ):
        raise ValueError("Unapproved error category")
    rows = sb(
        "PATCH", "cikgulaju_broadcast_deliveries?"
                 f"campaign_id=eq.{CAMPAIGN}&telegram_user_id=eq.{int(uid)}"
                 "&status=eq.sending",
        json={
            "status": status, "finished_at": datetime.now(timezone.utc).isoformat(),
            "error_code": category,
        },
        prefer="return=representation",
    )
    if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("status") != status:
        # A sent message with a failed DB write must NEVER be resent.
        raise RuntimeError("Delivery outcome could not be durably recorded")


def _send_one(api, uid, post=requests.post, pause=time.sleep):
    args = {
        "chat_id": uid, "text": ANNOUNCEMENT,
        "parse_mode": "HTML", "disable_web_page_preview": True,
        "reply_markup": WEB_KEYBOARD,
    }
    for attempt in range(2):
        try:
            response = post(api + "/sendMessage", json=args, timeout=13)
            body = response.json()
            if response.ok and isinstance(body, dict) and body.get("ok") is True:
                result = body.get("result") or {}
                if (isinstance(result, dict) and isinstance(result.get("message_id"), int)
                        and isinstance(result.get("chat"), dict)
                        and result["chat"].get("id") == uid):
                    return "sent", None
                return "failed", "unconfirmed"
            if response.status_code == 429:
                if attempt == 0:
                    params = body.get("parameters", {}) if isinstance(body, dict) else {}
                    wait = params.get("retry_after") if isinstance(params, dict) else None
                    pause(min(15, max(1, wait if type(wait) is int else 2)))
                    continue
                return "failed", "rate_limited"
            if response.status_code == 403:
                return "failed", "blocked"
            if response.status_code == 400:
                return "failed", "chat_missing"
            return "failed", "telegram_error"
        except (requests.RequestException, ValueError, TypeError, AttributeError):
            return "failed", "transport_error"
    return "failed", "rate_limited"


def install(runtime, *, preserve_referral=False):
    if getattr(runtime, "CIKGULAJU_BROADCAST_INSTALLED", False):
        return True
    if not all(callable(getattr(runtime, name, None))
               for name in ("_admin_panel", "callback", "_is_admin", "send", "_sb_request")):
        return False
    if not isinstance(getattr(runtime, "state", None), dict) or not getattr(runtime, "API", None):
        return False
    if not getattr(runtime, "CIKGULAJU_SUPABASE_USER_RECORDS_ACTIVE", True):
        # The durable _sb_request is the source of truth, never local SQLite.
        return False

    original_panel = runtime._admin_panel
    original_callback = runtime.callback
    send = runtime.send
    sb = runtime._sb_request

    def admin_notice(cid, message, buttons=None):
        return send(cid, message, buttons or [
            [{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}]])

    def finish_message(cid):
        try:
            progress = _status(sb)
            if progress is None:
                return admin_notice(cid, "📢 Hebahan Web belum pernah dihantar.",
                                    [[dict(BUTTON)], [{"text": "🛠️ Panel Admin",
                                                       "callback_data": "admin_panel"}]])
            lines = [
                "📊 <b>STATUS HEBAHAN WEB CIKGULAJU</b>",
                f"👥 Sasaran: <b>{progress['total']}</b>",
                f"✅ Berjaya: <b>{progress['sent']}</b>",
                f"⛔ Gagal/sekatan bot: <b>{progress['failed']}</b>",
                f"⏳ Belum dihantar: <b>{progress['queued']}</b>",
                f"🔍 Perlu semakan manual: <b>{progress['sending']}</b>",
            ]
            keyboard = [
                [{"text": "🔄 Refresh Status", "callback_data": "admin_web_broadcast|status"}],
            ]
            if progress["queued"]:
                keyboard.append([{
                    "text": "▶️ Sambung Penerima Belum Dihantar",
                    "callback_data": "admin_web_broadcast|resume",
                }])
            keyboard.append([{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}])
            return admin_notice(cid, "\n".join(lines), keyboard)
        except Exception as exc:
            print("WEB BROADCAST status unavailable:", type(exc).__name__, flush=True)
            return admin_notice(cid, "⚠️ Status hebahan tidak dapat dibaca dari Supabase. Tiada penghantaran dimulakan.")

    def _process(cid):
        try:
            # Multiple workers can run: the DB claim locks a unique queued user.
            with _SEND_LOCK:
                for _ in range(MAX_USERS):
                    uid = _next_recipient(sb)
                    if uid is None:
                        break
                    result, error = _send_one(runtime.API, uid)
                    _record(sb, uid, result, error)
                    time.sleep(DELAY_SECONDS)
        except Exception as exc:
            # Leave uncertain 'sending' deliveries untouched. Never auto-retry.
            print("WEB BROADCAST halted:", type(exc).__name__, flush=True)
            try:
                admin_notice(cid, "⚠️ Proses hebahan terhenti. Buka Status Hebahan untuk semak "
                               "penerima belum dihantar. Penerima dalam status semakan manual "
                               "tidak akan dihantar semula secara automatik.")
            except Exception:
                pass
        else:
            try:
                finish_message(cid)
            except Exception:
                pass

    def start(cid):
        worker = threading.Thread(
            target=_process, args=(cid,), daemon=True,
            name="cikgulaju-web-launch-announcement",
        )
        worker.start()

    def admin_panel(cid):
        result = original_panel(cid)
        if not runtime._is_admin(cid):
            return result
        try:
            payload = result.json() if result is not None else {}
            msg = payload.get("result") or {}
            message_id = msg.get("message_id")
            keyboard = (msg.get("reply_markup") or {}).get("inline_keyboard") or []
            if type(message_id) is not int or not keyboard:
                raise RuntimeError("Admin panel menu unavailable")
            if any(b.get("callback_data") == BUTTON["callback_data"]
                   for row in keyboard for b in row):
                return result
            rows = [[dict(b) for b in row] for row in keyboard]
            # The earlier referral-admin wrapper edits the same Telegram
            # message but returns the *original* sendMessage response.
            # Reinsert its known action so this final edit never erases it.
            referral_action = "admin_ref_points|list|0"
            if preserve_referral and not any(
                b.get("callback_data") == referral_action
                for row in rows for b in row
            ):
                rows.append([{"text": "📊 MATA REFERRAL",
                              "callback_data": referral_action}])
            before = next(
                (i for i, row in enumerate(rows)
                 if any(b.get("callback_data") == "admin_system" for b in row)),
                len(rows),
            )
            rows.insert(before, [dict(BUTTON)])
            reply = requests.post(
                runtime.API + "/editMessageReplyMarkup",
                json={"chat_id": cid, "message_id": message_id,
                      "reply_markup": {"inline_keyboard": rows}},
                timeout=10,
            )
            if not reply.ok or (reply.json() or {}).get("ok") is not True:
                raise RuntimeError("Telegram admin menu update rejected")
        except Exception as exc:
            # Never replace/remove any existing admin controls on failure.
            print("WEB BROADCAST admin menu fallback:", type(exc).__name__, flush=True)
            try:
                admin_notice(cid, "📢 <b>Hebahan Pengguna — Web CikguLaju</b>",
                             [[dict(BUTTON)]])
            except Exception:
                pass
        return result

    def callback(cid, data):
        raw = str(data or "")
        if not raw.startswith("admin_web_broadcast|"):
            return original_callback(cid, data)
        if not runtime._is_admin(cid):
            return admin_notice(cid, "⛔ Hebahan hanya untuk admin CikguLaju.")
        if raw != "admin_web_broadcast|preview" and raw not in _ACTIONS and not _CONFIRM.fullmatch(raw):
            return admin_notice(cid, "⚠️ Butang hebahan tidak sah.")
        if raw == "admin_web_broadcast|cancel":
            runtime.state.setdefault(cid, {}).pop("web_broadcast_preview", None)
            return admin_notice(cid, "✅ Hebahan dibatalkan. Tiada mesej dihantar.")
        if raw == "admin_web_broadcast|status":
            return finish_message(cid)
        if raw == "admin_web_broadcast|resume":
            try:
                result = _status(sb)
                if result is None:
                    return admin_notice(cid, "Tiada hebahan yang pernah disahkan.")
                if result["queued"] == 0:
                    return finish_message(cid)
                start(cid)
                return admin_notice(cid, "▶️ Proses dilanjutkan untuk penerima yang "
                                       "belum pernah dicuba. Tiada mesej diulang.")
            except Exception as exc:
                print("WEB BROADCAST resume failed:", type(exc).__name__, flush=True)
                return admin_notice(cid, "⚠️ Tidak dapat menyambung hebahan. Data sedia ada tidak berubah.")
        if raw == "admin_web_broadcast|preview":
            try:
                existing = _campaign(sb)
                if existing is not None:
                    return finish_message(cid)
                number = _ids(sb)
                if number < 1:
                    return admin_notice(cid, "⚠️ Tiada pengguna berdaftar untuk menerima hebahan.")
                nonce = secrets.token_hex(8)
                runtime.state.setdefault(cid, {})["web_broadcast_preview"] = {
                    "token": nonce, "timestamp": time.monotonic(),
                    "count": number,
                }
                return admin_notice(
                    cid, "📢 <b>PRATONTON HEBAHAN WEB</b>\n"
                         f"👥 Pengguna berdaftar: <b>{number}</b>\n"
                         "Tiada mesej dihantar sehingga anda tekan SAHKAN.\n\n"
                         + ANNOUNCEMENT,
                    [[{"text": f"✅ Sahkan & Hantar kepada {number} pengguna",
                       "callback_data": f"admin_web_broadcast|confirm|{nonce}"}],
                     [{"text": "❌ Batal", "callback_data": "admin_web_broadcast|cancel"}],
                     [{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}]],
                )
            except Exception as exc:
                print("WEB BROADCAST preview unavailable:", type(exc).__name__, flush=True)
                return admin_notice(cid, "⚠️ Senarai pengguna tidak dapat disahkan. Tiada mesej dihantar.")
        match = _CONFIRM.fullmatch(raw)
        if match:
            draft = runtime.state.setdefault(cid, {}).pop("web_broadcast_preview", None)
            if (not isinstance(draft, dict) or draft.get("token") != match.group(1)
                    or type(draft.get("count")) is not int
                    or not (0 <= time.monotonic() - draft.get("timestamp", -1e10) <= TTL_SECONDS)):
                return admin_notice(cid, "⚠️ Pratonton tamat atau butang telah digunakan. "
                                       "Buka Hebahan Pengguna semula.")
            try:
                # A single transactional DB function snapshots registered IDs
                # and prevents double-confirmation across workers/admins.
                confirmed = sb("POST", "rpc/cikgulaju_broadcast_prepare",
                               json={"p_campaign": CAMPAIGN,
                                     "p_admin": int(cid),
                                     "p_sha256": MESSAGE_SHA256,
                                     "p_expected_count": draft["count"]})
                if type(confirmed) is not int or confirmed != draft["count"]:
                    raise RuntimeError("Database did not confirm snapshot")
                start(cid)
                return admin_notice(
                    cid, f"📢 Hebahan dimulakan kepada <b>{confirmed}</b> pengguna "
                         "berdaftar. Penghantaran direkod satu demi satu di Supabase. "
                         "Tekan Status untuk laporan semasa.",
                    [[{"text": "📊 Status Hebahan", "callback_data": "admin_web_broadcast|status"}],
                     [{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}]],
                )
            except Exception as exc:
                print("WEB BROADCAST confirmation failed:", type(exc).__name__, flush=True)
                return admin_notice(
                    cid, "⚠️ Pengesahan hebahan tidak selesai. "
                         "Semak Status Hebahan sebelum cuba lagi. "
                         "Tiada mesej dihantar tanpa rekod pengesahan pangkalan data.",
                    [[{"text": "📊 Status Hebahan", "callback_data": "admin_web_broadcast|status"}],
                     [{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}]],
                )
        return admin_notice(cid, "⚠️ Tindakan hebahan tidak dikenali.")

    runtime._admin_panel = admin_panel
    runtime.callback = callback
    runtime.CIKGULAJU_BROADCAST_INSTALLED = True
    return True
