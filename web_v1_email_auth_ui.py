"""Production-only email login UI injection for the shared Web page."""
import os
from pathlib import Path

from flask import request, send_file


LOGIN_MARKER = '<div id="telegram-widget" aria-label="Log masuk Telegram"></div>'
LOGIN_HTML = """
<div id="email-auth-login" class="email-auth-box">
  <div class="email-auth-divider"><span>atau log masuk dengan emel</span></div>
  <label for="email-login-address">Alamat emel</label>
  <input id="email-login-address" type="email" autocomplete="email" maxlength="254" required>
  <label for="email-login-password">Kata laluan</label>
  <input id="email-login-password" type="password" autocomplete="current-password"
         minlength="8" maxlength="72" required>
  <div class="email-auth-actions">
    <button id="email-login-button" type="button">Log Masuk</button>
    <button id="email-register-button" type="button">Daftar Akaun Emel</button>
  </div>
  <p id="email-login-status" class="notice" role="status" aria-live="polite"></p>
  <p class="email-auth-help">Akaun Telegram boleh dipautkan dengan emel selepas log masuk Telegram.</p>
</div>
<style>
.email-auth-box{border-top:1px solid #e0eae6;margin-top:22px;padding-top:8px;text-align:left}
.email-auth-box input,.email-link-card input{display:block;width:100%;padding:13px;border:1px solid #ceded8;border-radius:12px;background:white;font:inherit}
.email-auth-divider{text-align:center;color:#718178;font-size:.85rem;margin:17px 0}
.email-auth-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}
.email-auth-actions button,.email-link-card button{border:0;border-radius:11px;padding:12px 14px;font:inherit;font-weight:700;cursor:pointer;background:#087568;color:#fff}
.email-auth-actions button:disabled,.email-link-card button:disabled{opacity:.55;cursor:wait}
.email-auth-actions button:last-child{background:#e6f5ee;color:#087568}
.email-auth-help{font-size:.85rem;margin-bottom:0}
.email-link-card{border:1px solid #dce8ef;border-radius:15px;padding:18px;margin:18px 0;background:#fbfdff}
.email-link-card h3{margin:0 0 8px;color:#174766}
.email-link-card label{display:block;margin:12px 0 6px;font-weight:700}
.email-link-card button{margin-top:13px}
@media(max-width:500px){.email-auth-actions{grid-template-columns:1fr}}
</style>
"""


def install(app):
    root = Path(__file__).resolve().parent
    script_path = root / "web_v1_static_preview" / "email-auth.js"

    def email_auth_script():
        response = send_file(script_path, mimetype="application/javascript",
                             max_age=300, conditional=True)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    app.add_url_rule("/assets/email-auth.js", "email_auth_script",
                     email_auth_script, methods=["GET"])

    @app.after_request
    def inject_email_auth(response):
        if (request.path != "/" or response.status_code != 200
                or response.mimetype != "text/html"
                or not os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()):
            return response
        try:
            response.direct_passthrough = False
            page = response.get_data(as_text=True)
        except Exception:
            return response
        if LOGIN_MARKER not in page:
            return response
        page = page.replace(LOGIN_MARKER, LOGIN_MARKER + LOGIN_HTML, 1)
        script_tag = '<script src="/assets/email-auth.js" defer></script>'
        if "</body>" in page and script_tag not in page:
            page = page.replace("</body>", script_tag + "</body>", 1)
        response.set_data(page)
        response.headers["Cache-Control"] = "no-store, private"
        return response
