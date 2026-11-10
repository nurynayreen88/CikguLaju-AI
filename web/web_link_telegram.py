"""Add one direct Web CikguLaju link to the existing Telegram main menu.

This is a narrow additive wrapper installed after all current menus, including
the user manual and private referral buttons. No curriculum/payment/state edits.
"""
import requests

WEB_URL = "https://cikgulaju-web.onrender.com/"
BUTTON = {"text": "🌐 Web CikguLaju", "url": WEB_URL}
TODAY_BUTTON = {"text": "⚡ RPH Hari Ini", "callback_data": "todayrph272"}


def install(runtime):
    if getattr(runtime, "CIKGULAJU_WEB_LINK_MENU_ACTIVE", False):
        return True
    if not callable(getattr(runtime, "menu", None)) or not callable(getattr(runtime, "send", None)):
        return False
    if not getattr(runtime, "API", None):
        return False
    old_menu = runtime.menu

    def menu(cid, show_persistent=False):
        response = old_menu(cid, show_persistent=show_persistent)
        try:
            result = response.json().get("result") or {}
            mid = result.get("message_id")
            kb = (result.get("reply_markup") or {}).get("inline_keyboard") or []
            if type(mid) is not int or mid < 1 or not isinstance(kb, list) or not kb:
                raise RuntimeError("Original menu unavailable")
            rows = [[dict(b) for b in row] for row in kb]
            changed = False
            # Add today's RPH in the SAME Telegram message as the main menu.
            # The special-activity flow remains under 📚 Sediakan RPH.
            if (getattr(runtime, "CIKGULAJU_DAILY_MANUAL_ONLY_20261110", False)
                    and not any(b.get("callback_data") == "todayrph272"
                                for row in rows for b in row)):
                after_rph = next(
                    (i + 1 for i, row in enumerate(rows)
                     if any(b.get("callback_data") == "quick"
                            or "Sediakan RPH" in b.get("text", "")
                            for b in row)), None)
                if after_rph is None:
                    after_rph = next(
                        (i for i, row in enumerate(rows)
                         if any(b.get("callback_data") == "account"
                                for b in row)), len(rows))
                rows.insert(after_rph, [dict(TODAY_BUTTON)])
                changed = True
            if not any(b.get("url") == WEB_URL for row in rows for b in row):
                index = next((i+1 for i, row in enumerate(rows)
                              if any(b.get("callback_data") == "account"
                                     for b in row)), len(rows))
                rows.insert(index, [dict(BUTTON)])
                changed = True
            if not changed:
                return response
            reply = requests.post(runtime.API + "/editMessageReplyMarkup",
                json={"chat_id": cid, "message_id": mid,
                      "reply_markup": {"inline_keyboard": rows}}, timeout=12)
            if not reply.ok or reply.json().get("ok") is not True:
                raise RuntimeError("Telegram rejected Web menu link")
        except Exception as exc:
            print("WEB MENU LINK fallback:", type(exc).__name__, flush=True)
            try:
                runtime.send(cid, "🌐 Buka CikguLaju di Web", [[dict(BUTTON)]])
            except Exception:
                pass
        return response

    runtime.menu = menu
    runtime.CIKGULAJU_WEB_LINK_MENU_ACTIVE = True
    return True
