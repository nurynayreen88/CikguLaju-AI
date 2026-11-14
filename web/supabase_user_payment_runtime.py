"""Supabase source of truth for Telegram users and payment-request workflow.

This replaces only user-owned data handlers when explicitly enabled. It never
modifies the curriculum database or credit/entitlement award logic. Payment IDs
are PostgreSQL identity values, stable across Render deploys. Supabase outages
fail closed: never silently fall back to a new/empty SQLite payment queue.
"""
import html
import os
from web.payment_receipt_admin_runtime import malaysia_time
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, timezone


def _telegram_proof_time(message):
    """Actual Telegram user submission UTC instant, not payment creation time."""
    now = datetime.now(timezone.utc)
    try:
        submitted = datetime.fromtimestamp(int(message["date"]), timezone.utc)
        if datetime(2020, 1, 1, tzinfo=timezone.utc) <= submitted <= now + timedelta(minutes=5):
            return submitted.isoformat()
    except (KeyError, TypeError, ValueError, OverflowError):
        pass
    return now.isoformat()


def enabled():
    return os.getenv("CIKGULAJU_SUPABASE_USER_RECORDS", "0").lower() in (
        "1", "true", "yes"
    )


def _first(result):
    if isinstance(result, list):
        return result[0] if result else None
    return result if isinstance(result, dict) else None


def _int_id(raw):
    value = int(raw)
    if value <= 0:
        raise ValueError("Invalid user or payment ID")
    return value


def _money(amount):
    try:
        amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid payment amount")
    if not Decimal("0") < amount <= Decimal("99999999.99"):
        raise ValueError("Payment amount out of range")
    return str(amount)


def install(runtime):
    if not enabled():
        return False
    sb = runtime._sb_request
    send = runtime.send
    original_counts = runtime._admin_counts
    original_list = runtime._admin_list
    original_upsert = runtime._upsert_user
    original_directory = runtime._admin_persistent_users

    def payment_request(request_id):
        pid = _int_id(request_id)
        rows = sb("GET", "bot_payment_requests?select=*&id=eq."
                  f"{pid}&limit=1")
        return _first(rows)

    def latest_pending_payment(chat_id):
        uid = _int_id(chat_id)
        rows = sb("GET", "bot_payment_requests?select=*&chat_id=eq."
                  f"{uid}&status=eq.pending&order=id.desc&limit=1")
        return _first(rows)

    def new_payment_request(chat_id, message_id=None, amount=5.00):
        uid = _int_id(chat_id)
        price = _money(amount)
        existing = latest_pending_payment(uid)
        if existing:
            return int(existing["id"])
        data = {"chat_id": str(uid), "amount": price,
                "telegram_message_id": int(message_id) if message_id else None}
        try:
            result = sb("POST", "bot_payment_requests", json=data,
                        prefer="return=representation")
        except Exception:
            # Unique pending index resolves concurrent requests idempotently;
            # if DB is actually unavailable, this read also fails closed.
            existing = latest_pending_payment(uid)
            if existing:
                return int(existing["id"])
            raise
        item = _first(result)
        if not item or not item.get("id"):
            raise RuntimeError("Supabase did not confirm payment request ID")
        return int(item["id"])

    def set_payment_note(request_id, note):
        pid = _int_id(request_id)
        payload = {"notes": str(note or "")[:2000]}
        # Preserve a Telegram file pointer to the receipt when the user sends
        # photo/PDF proof. Do not store raw receipt bytes or expose file_id.
        if str(note or "").startswith("proof_received"):
            current = payment_request(pid)
            if not current or current.get("status") != "pending":
                raise RuntimeError("Pending payment request no longer exists")
            try:
                update = runtime.request.get_json(silent=True) or {}
                message = update.get("message") or {}
                sender = message.get("from") or {}
                chat = message.get("chat") or {}
                if (str(chat.get("type")) == "private"
                        and str(chat.get("id")) == str(current["chat_id"])
                        and str(sender.get("id")) == str(current["chat_id"])):
                    photo = (message.get("photo") or [])
                    doc = message.get("document") or {}
                    if photo:
                        file = photo[-1]
                        mimetype = "telegram/photo"
                    elif doc:
                        file = doc
                        mimetype = str(doc.get("mime_type") or
                                       "application/octet-stream")[:100]
                    else:
                        file = {}
                        mimetype = None
                    if file.get("file_id"):
                        from datetime import datetime, timezone
                        payload.update({
                            "proof_telegram_file_id":str(file["file_id"]),
                            "proof_file_unique_id":str(file.get("file_unique_id") or ""),
                            "proof_telegram_message_id":int(message["message_id"]),
                            "proof_mime_type":mimetype,
                            "proof_received_at":_telegram_proof_time(message)
                        })
            except Exception as exc:
                print("DURABLE USER proof metadata unavailable:",
                      type(exc).__name__,flush=True)
        result = sb(
            "PATCH",
            f"bot_payment_requests?id=eq.{pid}&status=eq.pending",
            json=payload,
            prefer="return=representation"
        )
        if _first(result) is None:
            raise RuntimeError("Pending payment request no longer exists")
        return True

    def mark_payment_request(request_id, status, admin_cid="", notes=""):
        pid = _int_id(request_id)
        if status not in ("approved", "rejected"):
            raise ValueError("Invalid payment decision")
        current = payment_request(pid)
        if not current or current.get("status") != "pending":
            raise RuntimeError("Payment request is missing or already reviewed")
        if not admin_cid and status == "approved":
            raise ValueError("Payment approval requires admin ID")
        # Admin reviews are restricted; the one existing user-side
        # cancellation path may reject only its own still-pending request.
        is_admin = bool(admin_cid and runtime._is_admin(admin_cid))
        self_cancel = (
            status == "rejected"
            and str(notes or "") == "Cancelled by user before proof"
            and str(admin_cid or "") == str(current.get("chat_id"))
        )
        if not (is_admin or self_cancel):
            raise PermissionError("Payment review requires admin or owner cancellation")
        from datetime import datetime, timezone
        result = sb(
            "PATCH", f"bot_payment_requests?id=eq.{pid}&status=eq.pending",
            json={
                "status": status,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "reviewed_by": str(admin_cid or ""),
                "notes": str(notes or "")[:2000]
            }, prefer="return=representation"
        )
        if _first(result) is None:
            raise RuntimeError("Payment request changed before review")
        return True

    def review_rakan_payment(req, admin_cid, decision):
        if not runtime._is_admin(admin_cid):
            raise PermissionError("Rakan payment review requires admin")
        return _first(sb("POST", "rpc/review_rakan_payment", json={
            "p_payment_id": _int_id(req["id"]),
            "p_payer": _int_id(req["chat_id"]),
            "p_admin": _int_id(admin_cid),
            "p_proof_received_at": req.get("proof_received_at"),
            "p_decision": decision,
        }))

    def payment_counts():
        counts = _first(sb("POST", "rpc/bot_payment_status_counts", json={}))
        if not isinstance(counts, dict):
            raise RuntimeError("Payment count RPC unavailable")
        return {
            "pending": int(counts["pending"]),
            "approved": int(counts["approved"]),
            "rejected": int(counts["rejected"]),
        }

    def admin_counts():
        # Existing user/profile counts stay as before. Only payment counts
        # become authoritative Supabase values.
        result = dict(original_counts())
        counts = payment_counts()
        result["pending"] = counts["pending"]
        result["paid"] = counts["approved"]
        return result

    def admin_list(cid, kind="all", page=0):
        if kind not in ("pending", "payments"):
            return original_list(cid, kind, page)
        if not runtime._is_admin(cid):
            return send(cid, "⛔ Panel ini hanya untuk admin CikguLaju.")
        try:
            page = min(10000, max(0, int(page)))
            per = 8
            params = (
                "bot_payment_requests?select=id,chat_id,amount,status,"
                "submitted_at,proof_received_at&order=id.desc"
                f"&limit={per + 1}&offset={per * page}"
            )
            if kind == "pending":
                params += "&status=eq.pending"
            rows = sb("GET", params)
            if not isinstance(rows, list):
                raise RuntimeError("Payment list could not be read")
            people = {str(u.get("chat_id") or ""):u
                      for u in original_directory()}
            title = ("⏳ <b>PENDING PENGESAHAN — SUPABASE</b>" if kind == "pending"
                     else "💳 <b>SEJARAH BAYARAN — SUPABASE</b>")
            lines = [title, "", f"Halaman {page + 1}",
                     "Pilih rekod untuk menyemak ID pengguna dan status.", ""]
            buttons = []
            for payment in rows[:per]:
                uid = str(payment["chat_id"])
                person = people.get(uid) or {}
                name = runtime._admin_user_name(person)[:18]
                amount = _money(payment["amount"])
                icon = {"approved":"✅","pending":"⏳","rejected":"❌"}.get(
                    str(payment.get("status")), "•")
                lines.append(f"{icon} #{payment['id']} • ID <code>{uid}</code> "
                             f"• RM{amount}")
                lines.append("  🗓️ Permohonan: " +
                             malaysia_time(payment.get("submitted_at")))
                lines.append("  🧾 Resit: " +
                             malaysia_time(payment.get("proof_received_at")))
                label = f"{icon} #{payment['id']} {name} • RM{amount}"
                callback = (f"admin_pending|{int(payment['id'])}"
                            if kind == "pending"
                            else f"admin_user|{uid}")
                buttons.append([{"text": label, "callback_data": callback}])
            if not rows:
                lines.append("Tiada rekod pada halaman ini.")
            nav = []
            if page:
                nav.append({"text":"⬅️","callback_data":f"admin_list|{kind}|{page-1}"})
            nav.append({"text":"🛠️ PANEL","callback_data":"admin_panel"})
            if len(rows) > per:
                nav.append({"text":"➡️","callback_data":f"admin_list|{kind}|{page+1}"})
            buttons.append(nav)
            return send(cid,"\n".join(lines),buttons)
        except Exception as exc:
            print("DURABLE USER payment admin list error:",
                  type(exc).__name__, flush=True)
            return send(cid,
                "⚠️ Senarai pembayaran Supabase tidak tersedia. "
                "Tiada data ditetapkan kosong dan tiada kelulusan dibuat.",
                [[{"text":"🔄 Cuba Lagi","callback_data":f"admin_list|{kind}|0"}],
                 [{"text":"🛠️ Panel Admin","callback_data":"admin_panel"}]])

    def upsert_user(user, cid=None):
        created = original_upsert(user, cid)
        # Mirror optional Telegram names to existing persisted user records;
        # preserve user-selected teacher_profiles.display_name separately.
        user = user or {}
        uid = cid if cid is not None else user.get("id")
        try:
            uid = _int_id(uid)
            runtime._ensure_trial_user(uid)
            existing = _first(sb(
                "GET", f"cikgulaju_users?telegram_user_id=eq.{uid}"
                       "&select=username,first_name,last_name"
            ))
            if existing is None:
                raise RuntimeError("Supabase user creation not confirmed")
            payload = {}
            for field in ("username", "first_name", "last_name"):
                if field in user:
                    value = str(user.get(field) or "")[:150]
                    if value != str(existing.get(field) or ""):
                        payload[field] = value
            if payload:
                sb("PATCH", f"cikgulaju_users?telegram_user_id=eq.{uid}",
                   json=payload, prefer="return=minimal")
        except Exception as exc:
            # Identity metadata is non-financial. Keep working while reporting
            # failure; never grant payment/points on this fallback.
            print("DURABLE USER identity persistence warning:",
                  type(exc).__name__, flush=True)
        return created

    def admin_persistent_users():
        users = original_directory()
        by_id = {str(u.get("chat_id") or ""):dict(u) for u in users}
        offset = 0
        while True:
            rows = sb(
                "GET", "cikgulaju_users?select=telegram_user_id,"
                       "username,first_name,last_name,created_at,updated_at"
                       f"&order=telegram_user_id.asc&limit=500&offset={offset}"
            )
            if not isinstance(rows, list):
                raise RuntimeError("Durable user directory unavailable")
            for row in rows:
                uid = str(row["telegram_user_id"])
                existing = by_id.setdefault(uid,{"chat_id":uid})
                for field in ("username", "first_name", "last_name"):
                    if not existing.get(field) and row.get(field):
                        existing[field] = row[field]
                if not existing.get("created_at"):
                    existing["created_at"] = row.get("created_at")
                if not existing.get("last_seen"):
                    existing["last_seen"] = row.get("updated_at")
            offset += len(rows)
            if len(rows) < 500:
                break
            if offset > 10000:
                raise RuntimeError("Durable directory pagination limit reached")
        return list(by_id.values())

    runtime._payment_request = payment_request
    runtime._latest_pending_payment = latest_pending_payment
    runtime._new_payment_request = new_payment_request
    runtime._set_payment_note = set_payment_note
    runtime._mark_payment_request = mark_payment_request
    runtime._review_rakan_payment = review_rakan_payment
    runtime._admin_counts = admin_counts
    runtime._admin_list = admin_list
    runtime._upsert_user = upsert_user
    runtime._admin_persistent_users = admin_persistent_users
    print("DURABLE USER RECORDS: SUPABASE PAYMENT QUEUE ENABLED", flush=True)
    return True
