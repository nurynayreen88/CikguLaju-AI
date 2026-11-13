"""Read-only private referral points report in the existing Telegram admin panel.

No payments, referral memberships, subscription or credit data are mutated.
Admin permission is rechecked for every callback; all records stay server-side.
"""
import html
import re
import requests

from referral_points_telegram import format_points, point_lines, point_summary

_ADMIN_LIST = re.compile(r"^admin_ref_points[|]list[|]([0-9]{1,4})$")
_ADMIN_DETAIL = re.compile(r"^admin_ref_points[|]detail[|]([0-9]{1,20})$")
_PANEL_BUTTON = {"text": "📊 MATA REFERRAL", "callback_data": "admin_ref_points|list|0"}
_PAGE_SIZE = 8
_FETCH_SIZE = 200
_MAX_ROWS = 10000


def install(runtime):
    if not callable(getattr(runtime, "_private_referral_member", None)):
        return False
    if not callable(getattr(runtime, "_is_admin", None)):
        return False
    original_panel = runtime._admin_panel
    original_callback = runtime.callback
    send = runtime.send
    sb = runtime._sb_request

    def rows_for(table, uid, select, order=None):
        items = []
        while True:
            path = (f"{table}?referrer_user_id=eq.{int(uid)}"
                    f"&select={select}&limit={_FETCH_SIZE}&offset={len(items)}")
            if order:
                path += f"&order={order}"
            batch = sb("GET", path)
            if not isinstance(batch, list):
                raise RuntimeError("Referral summary unavailable")
            items.extend(batch)
            if len(items) > _MAX_ROWS:
                raise RuntimeError("Referral history exceeds report limit")
            if len(batch) < _FETCH_SIZE:
                return items

    def totals(uid):
        signups = rows_for("referral_signups", uid, "referred_user_id")
        events = rows_for("referral_point_events", uid,
                          "points_delta,referred_user_id,payment_kind,awarded_at",
                          order="awarded_at.desc")
        return len(signups), len(events), events

    def admin_list(cid, page):
        if page > 1000:
            return send(cid, "⚠️ Halaman tidak sah.")
        result = sb(
            "POST", "rpc/affiliate_admin_members",
            json={"p_page": page, "p_page_size": _PAGE_SIZE},
        )
        if not isinstance(result, dict) or not isinstance(result.get("items"), list):
            raise RuntimeError("Referral member list unavailable")
        members = result["items"]
        lines = [
            "📊 <b>MATA REFERRAL — ADMIN</b>",
            "",
            f"Halaman: <b>{page + 1}</b>",
            "",
        ]
        keyboard = []
        if not members:
            lines.append("Tiada peserta referral direkodkan." if page == 0
                         else "Tiada peserta pada halaman ini.")
        for member in members:
            uid = int(member["user_id"])
            name = html.escape(str(member.get("first_name") or "").strip()[:70])
            identity = f"{name} · <code>{uid}</code>" if name else f"ID <code>{uid}</code>"
            status = "✅" if member["enabled"] else "🔒"
            lines.append(f"{status} {identity}\n"
                         f"Baki <b>{format_points(member['balance'])}</b> mata · "
                         f"Boleh dituntut {format_points(member['available'])} · "
                         f"Dalam tuntutan {format_points(member['reserved'])} · "
                         f"Dibayar {format_points(member['paid'])}\n"
                         f"{int(member['registered_count'])} daftar · {int(member['payment_count'])} bayaran")
            keyboard.append([{
                "text": f"{status} Semak ID {uid}",
                "callback_data": f"admin_ref_points|detail|{uid}",
            }])
        nav = []
        if page:
            nav.append({"text": "⬅️", "callback_data": f"admin_ref_points|list|{page - 1}"})
        if result.get("more") is True and page < 1000:
            nav.append({"text": "➡️", "callback_data": f"admin_ref_points|list|{page + 1}"})
        if nav:
            keyboard.append(nav)
        keyboard.append([{"text": "🔄 Segarkan", "callback_data":
                          f"admin_ref_points|list|{page}"}])
        keyboard.append([{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}])
        return send(cid, "\n".join(lines), keyboard)

    def admin_detail(cid, uid):
        member = runtime._private_referral_member(uid)
        if not member:
            return send(cid, "⚠️ Pengguna ini bukan peserta referral.",
                        [[{"text": "⬅️ Senarai Referral",
                           "callback_data": "admin_ref_points|list|0"}]])
        registered, paid, events = totals(uid)
        points = point_summary(sb, uid)
        users = sb("GET", f"cikgulaju_users?telegram_user_id=eq.{uid}"
                   "&select=first_name,username") or []
        user = users[0] if users else {}
        name = " ".join(x for x in [
            str(user.get("first_name") or "").strip(),
            ("@" + str(user["username"]).strip()) if user.get("username") else ""
        ] if x)
        name = html.escape(name[:90]) if name else "Nama tidak tersedia"
        status = "AKTIF" if member["enabled"] else "DINYAH-AKTIFKAN"
        lines = [
            "👤 <b>REFERRAL — BUTIRAN ADMIN</b>",
            "",
            f"Nama: <b>{name}</b>",
            f"ID Telegram: <code>{uid}</code>",
            f"Status referral: <b>{status}</b>",
            f"Rakan mendaftar: <b>{registered}</b>",
            f"Bayaran layak direkodkan: <b>{paid}</b>",
            point_lines(points),
            "",
            "<b>5 ganjaran terakhir</b>",
        ]
        for e in events[:5]:
            payment_kind = "Rakan Pembangun" if e["payment_kind"] == "pioneer" else "Langganan"
            lines.append(
                f"• +{format_points(e['points_delta'])} mata — "
                f"{payment_kind}, ID {int(e['referred_user_id'])}"
            )
        if not events:
            lines.append("Belum ada bayaran yang layak.")
        keyboard = [
            [{"text": "🔄 Segarkan", "callback_data":
              f"admin_ref_points|detail|{uid}"}],
            [{"text": "⬅️ Senarai Referral", "callback_data":
              "admin_ref_points|list|0"}],
            [{"text": "🛠️ Panel Admin", "callback_data": "admin_panel"}],
        ]
        return send(cid, "\n".join(lines), keyboard)

    def admin_panel(cid):
        response = original_panel(cid)
        if not runtime._is_admin(cid):
            return response
        try:
            data = response.json() if response is not None else {}
            result = data.get("result") or {}
            mid = result.get("message_id")
            keyboard = (result.get("reply_markup") or {}).get("inline_keyboard") or []
            if not mid or not keyboard:
                raise ValueError("No admin panel inline keyboard")
            if any(button.get("callback_data") == _PANEL_BUTTON["callback_data"]
                   for row in keyboard for button in row):
                return response
            updated = [list(row) for row in keyboard]
            # Insert before system status/refresh, preserving existing panel actions.
            before = next((i for i, row in enumerate(updated)
                           if any(b.get("callback_data") == "admin_system"
                                  for b in row)), len(updated))
            updated.insert(before, [dict(_PANEL_BUTTON)])
            res = requests.post(str(runtime.API) + "/editMessageReplyMarkup",
                                json={"chat_id": cid, "message_id": mid,
                                      "reply_markup": {"inline_keyboard": updated}},
                                timeout=12)
            if not res.ok or (res.json() or {}).get("ok") is not True:
                raise RuntimeError("Telegram markup edit rejected")
        except Exception as exc:
            # Do not lose the original admin panel; add a separate action on failure.
            print("PRIVATE REFERRAL admin panel button fallback:",
                  type(exc).__name__, flush=True)
            try:
                send(cid, "📊 <b>Semakan Mata Referral</b>",
                     [[dict(_PANEL_BUTTON)]])
            except Exception:
                pass
        return response

    def callback(cid, d):
        raw = str(d or "")
        if not raw.startswith("admin_ref_points|"):
            return original_callback(cid, d)
        if not runtime._is_admin(cid):
            return send(cid, "⛔ Paparan mata semua peserta hanya untuk admin.")
        try:
            match = _ADMIN_LIST.fullmatch(raw)
            if match:
                return admin_list(cid, int(match.group(1)))
            match = _ADMIN_DETAIL.fullmatch(raw)
            if match:
                return admin_detail(cid, int(match.group(1)))
            return send(cid, "⚠️ Butang referral tidak sah.")
        except Exception as exc:
            print("PRIVATE REFERRAL admin points report error:",
                  type(exc).__name__, flush=True)
            return send(cid, "⚠️ Rekod mata referral belum dapat disemak. "
                        "Cuba semula; tiada data diubah.")

    runtime._admin_panel = admin_panel
    runtime.callback = callback
    return True
