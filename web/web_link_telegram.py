"""Add one direct Web CikguLaju link to the existing Telegram main menu.

This is a narrow additive wrapper installed after all current menus, including
the user manual and private referral buttons. No curriculum/payment/state edits.
"""
import requests

WEB_URL = "https://cikgulaju-web.onrender.com/"
BUTTON = {"text": "🌐 Web CikguLaju", "url": WEB_URL}


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
            if any(b.get("url") == WEB_URL for row in kb for b in row):
                return response
            rows = [[dict(b) for b in row] for row in kb]
            index = next((i+1 for i, row in enumerate(rows)
                          if any(b.get("callback_data") == "account" for b in row)),len(rows))
            rows.insert(index, [dict(BUTTON)])
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
