"""Production-only email login UI injection for the shared Web page."""
import os
from pathlib import Path

from flask import request, send_file


LOGIN_MARKER = '<div id="telegram-widget" aria-label="Log masuk Telegram"></div>'
LOGIN_HTML = """
<section id="email-auth-login" class="email-auth-box" aria-labelledby="email-auth-title">
  <div class="email-auth-heading">
    <span class="email-auth-kicker">SELAMAT DATANG KE CIKGULAJU</span>
    <h2 id="email-auth-title">Akaun guru</h2>
    <p>Gunakan e-mel untuk masuk, atau daftar akaun baharu tanpa Telegram.</p>
  </div>
  <div class="email-auth-tabs" role="tablist" aria-label="Log masuk atau daftar akaun">
    <button id="email-mode-login" type="button" role="tab" aria-selected="true" aria-controls="email-auth-form" class="is-active">Log Masuk</button>
    <button id="email-mode-register" type="button" role="tab" aria-selected="false" aria-controls="email-auth-form">Daftar Baharu</button>
  </div>
  <form id="email-auth-form" novalidate>
    <p id="email-auth-explainer" class="email-auth-explainer">Sudah mempunyai akaun? Masukkan e-mel dan kata laluan.</p>
    <label for="email-login-address">Alamat e-mel</label>
    <input id="email-login-address" type="email" inputmode="email" autocomplete="email"
           placeholder="contoh@gmail.com" maxlength="254" required>
    <label for="email-login-password">Kata laluan</label>
    <div class="email-password-wrap">
      <input id="email-login-password" type="password" autocomplete="current-password"
             placeholder="Masukkan kata laluan" minlength="8" maxlength="72" required>
      <button id="email-password-toggle" type="button" aria-label="Tunjukkan kata laluan" aria-pressed="false">Lihat</button>
    </div>
    <div id="email-register-confirm-wrap" hidden>
      <label for="email-register-confirm">Ulang kata laluan</label>
      <input id="email-register-confirm" type="password" autocomplete="new-password"
             placeholder="Taip semula kata laluan" minlength="8" maxlength="72">
      <p class="email-auth-help">Gunakan sekurang-kurangnya 8 aksara. Jika perlu, sahkan alamat e-mel melalui pautan yang dihantar.</p>
    </div>
    <div class="email-auth-remember-line">
      <label class="email-auth-remember" for="email-remember-me">
        <input id="email-remember-me" type="checkbox" value="1">
        <span>Ingat saya selama 14 hari</span>
      </label>
      <button id="email-forgot-button" class="email-forgot-button" type="button">Lupa kata laluan?</button>
    </div>
    <p class="email-auth-help">Untuk peranti sendiri sahaja. Kata laluan tidak disimpan oleh pilihan ini.</p>
    <div class="email-auth-actions">
      <button id="email-login-button" type="submit">Log Masuk</button>
      <button id="email-register-button" type="submit" hidden>Daftar Akaun</button>
    </div>
  </form>
  <p id="email-login-status" class="notice email-auth-status" role="status" aria-live="polite"></p>
</section>
<div class="email-auth-divider"><span>ATAU</span></div>
<div class="email-auth-telegram-note">
  <strong>Ada akaun Telegram CikguLaju?</strong>
  <span>Log masuk dengan Telegram di bawah. Pilihan “Ingat saya” di atas turut digunakan.</span>
</div>
<style>
.email-auth-box{border:1px solid #d5e8e2;background:linear-gradient(145deg,#fff 50%,#f1faf7);border-radius:20px;margin:18px 0 12px;padding:23px;text-align:left;box-shadow:0 9px 30px rgba(21,75,59,.06)}
.email-auth-heading{margin-bottom:16px}
.email-auth-kicker{display:inline-flex;background:#e3f4eb;color:#087568;border-radius:30px;padding:6px 10px;font-size:.69rem;font-weight:800;letter-spacing:.08em;margin-bottom:9px}
.email-auth-box h2{font-size:1.28rem;line-height:1.3;letter-spacing:-.025em;color:#173d37;margin:0 0 6px}
.email-auth-box p{margin-top:6px;margin-bottom:8px;line-height:1.5}
.email-auth-tabs{display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:4px;border-radius:13px;background:#eaf3ef}
.email-auth-tabs button{border:0;border-radius:10px;padding:12px 9px;min-height:45px;font:inherit;font-size:.94rem;font-weight:800;cursor:pointer;background:transparent;color:#48665c}
.email-auth-tabs button.is-active{background:#fff;color:#096851;box-shadow:0 2px 9px rgba(18,71,53,.11)}
.email-auth-tabs button:focus-visible,.email-auth-box button:focus-visible{outline:3px solid #87c8b1;outline-offset:2px}
.email-auth-explainer{font-size:.87rem;color:#60766d;padding:8px 0 2px}
.email-auth-box input:not([type=checkbox]),.email-link-card input{display:block;width:100%;box-sizing:border-box;min-height:48px;padding:12px 13px;border:1px solid #c6d8d0;border-radius:11px;background:#fff;color:#18372e;font:inherit}
.email-auth-box input:not([type=checkbox]):focus,.email-link-card input:focus{outline:3px solid #0875682b;border-color:#087568}
.email-auth-box label:not(.email-auth-remember),.email-link-card label{display:block;margin:12px 0 6px;font-weight:700}
.email-password-wrap{display:flex;align-items:center;position:relative}
.email-password-wrap input{padding-right:75px!important}
#email-password-toggle{position:absolute;right:6px;top:5px;min-height:37px;border:0;border-radius:8px;padding:0 10px;background:#eef7f2;color:#176e55;font:inherit;font-size:.83rem;font-weight:800;cursor:pointer}
.email-auth-remember-line{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-top:14px}
.email-auth-remember{display:flex;align-items:center;gap:9px;cursor:pointer;font-size:.87rem;font-weight:650;color:#244e41}
.email-auth-remember input{appearance:auto;width:18px;height:18px;margin:0;accent-color:#087568}
.email-auth-help{font-size:.81rem;color:#60766d;line-height:1.5}
.email-auth-actions{display:block;margin-top:13px}
.email-auth-actions button,.email-link-card button{min-height:48px;width:100%;border:0;border-radius:11px;padding:11px 14px;font:inherit;font-weight:800;cursor:pointer;background:#087568;color:#fff}
.email-auth-actions button[hidden]{display:none}
.email-auth-actions button:disabled,.email-link-card button:disabled{opacity:.55;cursor:wait}
.email-forgot-button{margin:0;padding:5px 0;border:0;background:transparent;color:#087568;font:inherit;font-size:.85rem;font-weight:750;text-decoration:underline;cursor:pointer}
.email-auth-box [hidden]{display:none!important}
.email-auth-status:not(:empty){padding:9px 12px;margin-top:12px;border-radius:9px;background:#eff8f4}
.email-auth-reset{padding:4px 0}.email-auth-reset h2{margin:0 0 8px;color:#173d37}.email-auth-reset p{line-height:1.55}.email-auth-reset input{margin:8px 0 12px}
.email-auth-telegram-note{text-align:center;font-size:.86rem;margin:13px auto 6px;line-height:1.5;display:flex;flex-direction:column;gap:3px;color:#52685e}
.email-auth-telegram-note strong{color:#204c3e}
.email-auth-divider{display:flex;align-items:center;gap:12px;margin:14px 0 5px;text-align:center;color:#718178;font-size:.76rem;font-weight:800}
.email-auth-divider:before,.email-auth-divider:after{content:"";height:1px;background:#d9e5df;flex:1}
#telegram-widget{display:flex;justify-content:center;margin:8px 0}
.email-link-card{border:1px solid #dce8ef;border-radius:15px;padding:18px;margin:18px 0;background:#fbfdff}
.email-link-card h3{margin:0 0 8px;color:#174766}
.email-link-card button{margin-top:13px}
@media(max-width:500px){.email-auth-box{padding:16px}.email-auth-remember-line{align-items:flex-start}.email-auth-tabs button{font-size:.9rem}}
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
        # Telegram's user payload remains HMAC-verified; this opt-in UI field
        # is removed server-side before signature verification.
        page = page.replace(
            'body:JSON.stringify(user)',
            'body:JSON.stringify({...user,remember_me:document.getElementById("email-remember-me")?.checked===true})',
            1)
        script_tag = '<script src="/assets/email-auth.js" defer></script>'
        if "</body>" in page and script_tag not in page:
            page = page.replace("</body>", script_tag + "</body>", 1)
        response.set_data(page)
        response.headers["Cache-Control"] = "no-store, private"
        return response
