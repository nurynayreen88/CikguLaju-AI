"""Production-only email login UI injection for the shared Web page."""
import os
from pathlib import Path

from flask import request, send_file


LOGIN_MARKER = '<div id="telegram-widget" aria-label="Log masuk Telegram"></div>'
LOGIN_HTML = """
<div id="email-auth-login" class="email-auth-box">
  <div class="email-auth-heading">
    <span class="email-auth-kicker">MULA DI SINI</span>
    <h2>Daftar atau log masuk dengan emel</h2>
    <p>Pengguna baharu boleh terus mendaftar tanpa akaun Telegram. Akaun baharu mendapat 10 janaan RPH percuma.</p>
  </div>
  <label for="email-login-address">Alamat emel</label>
  <input id="email-login-address" type="email" autocomplete="email"
         placeholder="nama@gmail.com" maxlength="254" required>
  <label for="email-login-password">Kata laluan</label>
  <input id="email-login-password" type="password" autocomplete="current-password"
         placeholder="Sekurang-kurangnya 8 aksara" minlength="8" maxlength="72" required>
  <div class="email-auth-actions">
    <button id="email-register-button" type="button">Daftar Akaun Emel</button>
    <button id="email-login-button" type="button">Log Masuk Emel</button>
  </div>
  <button id="email-forgot-button" class="email-forgot-button" type="button">Lupa kata laluan?</button>
  <p class="email-auth-help">Jika diminta, sahkan emel melalui pautan yang dihantar. Akaun Telegram sedia ada boleh dipautkan kemudian.</p>
  <p id="email-login-status" class="notice" role="status" aria-live="polite"></p>
</div>
<p class="email-auth-telegram-note">Sudah menggunakan Telegram? Log masuk melalui pilihan di bawah.</p>
<div class="email-auth-divider"><span>ATAU LOG MASUK DENGAN TELEGRAM</span></div>
<style>
.email-auth-box{border:1px solid #d9ebe5;background:linear-gradient(145deg,#fff 65%,#f5fbf8);border-radius:18px;margin:20px 0 12px;padding:20px;text-align:left}
.email-auth-heading{margin-bottom:14px}
.email-auth-kicker{display:inline-flex;background:#e6f5ee;color:#087568;border-radius:30px;padding:6px 10px;font-size:.72rem;font-weight:800;letter-spacing:.08em;margin-bottom:8px}
.email-auth-box h2{font-size:1.18rem;line-height:1.3;letter-spacing:-.02em;color:#173d37;margin:0 0 7px}
.email-auth-box p{margin-top:6px;margin-bottom:8px}
.email-auth-box input,.email-link-card input{display:block;width:100%;padding:13px;border:1px solid #ceded8;border-radius:12px;background:white;font:inherit}
.email-auth-box input:focus,.email-link-card input:focus{outline:3px solid #0875682b;border-color:#087568}
.email-auth-box label,.email-link-card label{display:block;margin:13px 0 6px;font-weight:700}
.email-auth-actions{display:grid;grid-template-columns:1.15fr 1fr;gap:10px;margin-top:14px}
.email-auth-actions button,.email-link-card button{min-height:46px;border:0;border-radius:11px;padding:11px 14px;font:inherit;font-weight:750;cursor:pointer;background:#087568;color:#fff}
.email-auth-actions button:disabled,.email-link-card button:disabled{opacity:.55;cursor:wait}
.email-auth-actions button:last-child{background:#e6f5ee;color:#087568;border:1px solid #cfe9dd}
.email-auth-help{font-size:.82rem;color:#60766d;line-height:1.5}
.email-forgot-button{display:block;margin:8px 0 0 auto;padding:5px 2px;border:0;background:transparent;color:#087568;font:inherit;font-size:.86rem;font-weight:700;text-decoration:underline;cursor:pointer}
.email-auth-reset{padding:4px 0}.email-auth-reset h2{margin:0 0 8px;color:#173d37}.email-auth-reset p{line-height:1.55}.email-auth-reset input{margin:8px 0 12px}
.email-auth-telegram-note{text-align:center;font-size:.88rem;margin:14px 0 4px!important}
.email-auth-divider{text-align:center;color:#718178;font-size:.73rem;font-weight:800;letter-spacing:.06em;margin:8px 0}
#telegram-widget{display:flex;justify-content:center;margin:8px 0}
.email-link-card{border:1px solid #dce8ef;border-radius:15px;padding:18px;margin:18px 0;background:#fbfdff}
.email-link-card h3{margin:0 0 8px;color:#174766}
.email-link-card button{margin-top:13px}
@media(max-width:500px){.email-auth-box{padding:16px}.email-auth-actions{grid-template-columns:1fr}}
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

        page = page.replace(
            "<h1>Sediakan RPH langkah demi langkah</h1>",
            "<h1>RPH dan RPT 2027 lebih mudah diurus</h1>", 1)
        page = page.replace(
            "<p>Log masuk dengan akaun Telegram CikguLaju. Pilih Tahun, Subjek, Unit/Tajuk dan Lesson/PdP, kemudian jana RPH Word atau PDF terus menggunakan penjana Telegram.</p>",
            "<p>Daftar dengan emel untuk mula mencuba CikguLaju AI. Pilih tahun, subjek dan Lesson/PdP untuk menyediakan RPH, gunakan RPH Hari Ini, serta akses RPT 2027 mengikut pelan anda.</p>", 1)
        page = page.replace(
            'status.textContent="Sahkan akaun Telegram untuk meneruskan.";',
            'status.textContent="Akaun emel boleh digunakan melalui borang di atas. Log masuk Telegram ialah pilihan lain.";')
        page = page.replace(
            'status.textContent="Log masuk Telegram belum diaktifkan pada pelayan web.";',
            'status.textContent="Log masuk Telegram belum tersedia. Akaun emel boleh digunakan melalui borang di atas.";')
        page = page.replace(
            'status.textContent=error.name==="AbortError"?"Semakan Telegram mengambil masa terlalu lama. Akaun emel boleh digunakan melalui borang di atas.":"Sambungan Telegram belum tersedia. Akaun emel boleh digunakan melalui borang di atas."; ',
            'status.textContent=error.name==="AbortError"?"Semakan Telegram mengambil masa terlalu lama. Akaun emel boleh digunakan melalui borang di atas.":"Sambungan Telegram belum tersedia. Akaun emel boleh digunakan melalui borang di atas.";')
        page = page.replace(LOGIN_MARKER, LOGIN_HTML + LOGIN_MARKER, 1)
        script_tag = '<script src="/assets/email-auth.js" defer></script>'
        if "</body>" in page and script_tag not in page:
            page = page.replace("</body>", script_tag + "</body>", 1)
        response.set_data(page)
        response.headers["Cache-Control"] = "no-store, private"
        return response
