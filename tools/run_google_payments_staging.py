"""Isolated Google-first CikguLaju Web staging service.

Deploy ONLY on a separate Render service with a dedicated staging Supabase.
This entrypoint imports no Telegram production app, Web production launcher,
RPH generator, or legacy payment routes.
Start command:
  gunicorn --bind 0.0.0.0:$PORT tools.run_google_payments_staging:app
"""
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from web.google_auth_staging_routes import bp as google_login_bp
from web.google_payment_staging_routes import bp as google_payment_bp
from web.google_staging_admin_auth_routes import bp as admin_login_bp
from web.google_web_catalog_staging import bp as google_web_catalog_bp
from web.google_rph_bundle_delivery import bp as google_private_rph_delivery_bp

app=Flask(__name__)
# Render's HTTPS proxy supplies one trusted X-Forwarded-Proto hop. We never
# trust X-Forwarded-Host; every sensitive route verifies its exact host.
app.wsgi_app=ProxyFix(app.wsgi_app,x_proto=1)
app.register_blueprint(google_login_bp)
app.register_blueprint(admin_login_bp)
app.register_blueprint(google_payment_bp)
app.register_blueprint(google_web_catalog_bp)
app.register_blueprint(google_private_rph_delivery_bp)


@app.get("/")
def staging_index():
    from flask import redirect
    return redirect("/google-staging-login",code=302)


@app.get("/healthz")
def liveness():
    return jsonify({"service":"cikgulaju-google-payments-staging","live":True,
                    "production":False,"real_payments_enabled":False})


@app.get("/readyz")
def readiness():
    from web.google_auth_staging_routes import _enabled_config
    from web.google_staging_admin_auth_routes import _config as admin_config
    # Teachers can use Google without a Telegram identity. Admin Telegram
    # setup is a separate readiness dimension, not a login blocker.
    google_ready = bool(_enabled_config())
    admin_ready = bool(admin_config())
    return jsonify({"service":"cikgulaju-google-payments-staging",
                    "configured":google_ready,
                    "google_login_configured":google_ready,
                    "admin_review_configured":admin_ready,
                    "real_payments_enabled":False,
                    "rph_generator_enabled":False,
                    "no_telegram_production_account_dependency":True}), (200 if google_ready else 503)


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options","nosniff")
    response.headers.setdefault("Referrer-Policy","same-origin")
    response.headers.setdefault("X-Frame-Options","SAMEORIGIN")
    response.headers.setdefault("Strict-Transport-Security","max-age=31536000")
    return response
