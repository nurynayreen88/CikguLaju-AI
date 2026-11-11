"""Supabase-backed admin payment history page.

Integration: in _admin_list, after checking _is_admin(cid), handle
kind == 'payments' by calling show_admin_payment_history(cid, page,
_sb_request, send). Return immediately. This avoids reading the ephemeral
SQLite payment_requests table. The app's existing handler must be edited and
tested separately before this is live.
"""
import html
from decimal import Decimal, InvalidOperation
from supabase_admin_payment_history import fetch_admin_payment_history


def show_admin_payment_history(cid, page, request, send):
    try:
        page = max(0, min(int(page), 499))
    except (TypeError, ValueError, OverflowError):
        page = 0
    per = 8
    try:
        rows = fetch_admin_payment_history(request, limit=1000)
    except Exception:
        return send(cid, "⚠️ Sejarah bayaran tidak dapat dibaca daripada Supabase. Sila cuba lagi.",
                    [[{"text": "🔄 Cuba lagi", "callback_data": f"admin_list|payments|{page}"},
                      {"text": "🛠️ Panel", "callback_data": "admin_panel"}]])
    start = page * per
    selected = rows[start:start + per]
    lines = ["💳 <b>SEJARAH BAYARAN (SUPABASE)</b>", f"Halaman {page + 1}"]
    buttons = []
    for row in selected:
        uid = str(row.get("telegram_user_id") or "")
        amount = row.get("amount_rm")
        try:
            value = Decimal(str(amount)) if amount is not None else None
            money = f"RM{value:.2f}" if value is not None and value.is_finite() and value >= 0 else ("jumlah tidak direkod" if value is None else "jumlah tidak sah")
        except (TypeError, ValueError, OverflowError, InvalidOperation):
            money = "jumlah tidak sah"
        kind = row["kind"]
        if kind == "rakan_pembangun_request":
            kind = "Rakan Pembangun (permintaan bayaran, bukan resit)"
        elif kind == "rakan_pembangun_approval":
            kind = "Rakan Pembangun (kelulusan akses, bukan resit)"
        elif not row["is_receipt"]:
            kind = f"{kind} (belum disahkan sebagai bayaran)"
        lines.append(f"• {html.escape(str(kind))}: {html.escape(money)} | {html.escape(str(row['status']))} | ID {html.escape(uid[-6:])}")
        if uid.isascii() and uid.isdigit() and len(uid) <= 20:
            buttons.append([{"text": f"👤 ID {uid[-6:]}", "callback_data": f"admin_user|{uid}"}])
    if not selected:
        lines.append("Tiada rekod pada halaman ini.")
    nav = []
    if page:
        nav.append({"text": "⬅️", "callback_data": f"admin_list|payments|{page-1}"})
    nav.append({"text": "🛠️ Panel", "callback_data": "admin_panel"})
    if start + per < len(rows):
        nav.append({"text": "➡️", "callback_data": f"admin_list|payments|{page+1}"})
    buttons.append(nav)
    return send(cid, "\n".join(lines), buttons)
