"""Teacher-account download rehearsal on the existing isolated Google staging."""
import base64
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from flask import Blueprint, abort, redirect, render_template_string, request, send_file

from web.google_rph_generation_staging_routes import _generator_config, _test_actor_allowed
from web.google_web_catalog_staging import _actor

bp = Blueprint("english_y5_release_preview", __name__)
STAGING_HOST = "cikgulaju-google-payments-staging.onrender.com"
BASE = "/google-staging/english-year5-2027"
DATA = Path(__file__).with_name("english_y5_release_preview_samples.json")
LESSONS = {1: "001-002", 2: "001-002", 155: "155-156", 156: "155-156"}
MIME = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}
PAGE = """<!doctype html>
<html lang="ms"><head><meta charset="utf-8"><meta name="viewport"
content="width=device-width,initial-scale=1"><title>Ujian muat turun English Year 5</title>
<style>body {font: 1rem/1.6 system-ui,sans-serif;max-width: 38rem;
margin: 2rem auto;padding: 0 1rem} li {margin: .45rem 0}</style></head>
<body><main><h1>Ujian muat turun English Year 5</h1>
<p>Dua contoh RPH gabungan edisi Oktober 2027. Muat turun ujian ini tidak
menggunakan kredit.</p>
<ul>{% for lesson, pair in lessons.items() %}
<li>Lesson {{ "%03d" | format(lesson) }} (RPH {{ pair }})
— <a href="{{ base }}/{{ lesson }}.docx">Word</a>
· <a href="{{ base }}/{{ lesson }}.pdf">PDF</a></li>{% endfor %}</ul>
</main></body></html>"""


@bp.after_request
def private_download(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _check_account(*, page=False):
    if not request.is_secure or request.host != STAGING_HOST:
        abort(404)
    if _generator_config() is None:
        abort(503)
    actor, error = _actor()
    if error is not None:
        if page and error[1] == 401:
            return redirect("/google-staging-login", code=303)
        return error
    if not _test_actor_allowed(actor):
        abort(403)
    return None


@bp.get(BASE)
def preview():
    error = _check_account(page=True)
    if error is not None:
        return error
    return render_template_string(PAGE, base=BASE, lessons=LESSONS)


@bp.get(BASE + "/<int:lesson>.<extension>")
def download(lesson, extension):
    error = _check_account()
    if error is not None:
        return error
    pair = LESSONS.get(lesson)
    if pair is None or extension not in MIME:
        abort(404)
    try:
        source = json.loads(DATA.read_text(encoding="utf-8"))
        record = source["documents"][pair][extension]
        data = base64.b64decode(record["data_b64"], validate=True)
        digest = sha256(data).hexdigest()
        if digest != record["sha256"]:
            abort(503)
    except (OSError, TypeError, ValueError, KeyError):
        abort(503)
    response = send_file(BytesIO(data), mimetype=MIME[extension], as_attachment=True,
                         download_name=f"RPH_English_SK_2027_Y5_L{pair}.{extension}",
                         conditional=False)
    response.headers["X-RPH-Preview-Source-Commit"] = source["source_commit"]
    response.headers["X-RPH-Preview-SHA256"] = digest
    return response
