"""Deliver approved Science Year 4 samples to the existing staging teacher."""

import base64
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from flask import Blueprint, abort, render_template_string, send_file, url_for

from web.english_y5_release_preview import MIME, _check_account, private_download

bp = Blueprint("science_y4_release_preview", __name__)
bp.after_request(private_download)

BASE = "/google-staging/science-dlp-year4-2027"
DATA = Path(__file__).with_name("science_y4_release_preview_samples.json")
SOURCE_COMMIT = "786f6980fc3ab067ef99efbdb7b1c0ed677030e9"
LESSONS = {
    "lesson-46": ("DLP-SCI-Y4-L46", "Lesson 46 · Trace materials to their sources"),
    "review-08": ("DLP-SCI-Y4-R08", "Review 08 · Materials Review"),
}
PAGE = """<!doctype html>
<html lang="ms">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ujian muat turun Sains DLP Tahun 4</title>
<style>
body {font: 1rem/1.6 system-ui, sans-serif; max-width: 38rem; margin: 2rem auto; padding: 0 1rem}
li {margin: .6rem 0}
</style></head>
<body><main>
<h1>Ujian muat turun Sains DLP Tahun 4</h1>
<p>RPH 2027, versi {{ version }}. Muat turun ujian ini tidak menggunakan kredit.</p>
<ul>{% for label, word, pdf in files %}
<li>{{ label }} · <a href="{{ word }}">Word</a> · <a href="{{ pdf }}">PDF</a></li>
{% endfor %}</ul>
</main></body></html>"""


@bp.get(BASE)
def preview():
    error = _check_account(page=True)
    if error is not None:
        return error
    files = [
        (title, url_for(".download", lesson=lesson, extension="docx"),
         url_for(".download", lesson=lesson, extension="pdf"))
        for lesson, (_, title) in LESSONS.items()
    ]
    return render_template_string(PAGE, files=files, version=SOURCE_COMMIT[:7])


@bp.get(BASE + "/<lesson>.<extension>")
def download(lesson, extension):
    error = _check_account()
    if error is not None:
        return error
    if lesson not in LESSONS or extension not in MIME:
        abort(404)
    try:
        manifest = json.loads(DATA.read_text(encoding="utf-8"))
        if manifest["source_commit"] != SOURCE_COMMIT:
            abort(503)
        record = manifest["documents"][lesson][extension]
        data = base64.b64decode(record["data_b64"], validate=True)
        digest = sha256(data).hexdigest()
        if digest != record["sha256"]:
            abort(503)
    except (OSError, TypeError, ValueError, KeyError):
        abort(503)
    lesson_id, _ = LESSONS[lesson]
    response = send_file(BytesIO(data), mimetype=MIME[extension], as_attachment=True,
                         download_name=f"CIKGULAJU_RPH_{lesson_id}.{extension}", conditional=False)
    response.headers["X-RPH-Preview-Source-Commit"] = SOURCE_COMMIT
    response.headers["X-RPH-Preview-SHA256"] = digest
    return response
