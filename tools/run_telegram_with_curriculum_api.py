"""Optional production-compatible WSGI entrypoint for reviewed deployment.

Not active until the Render start command is explicitly changed from
'gunicorn app:app' to 'gunicorn tools.run_telegram_with_curriculum_api:app'.
No database copies, migrations, webhook registration, or bot token changes.
"""
import app as telegram_runtime
from web.register_curriculum_api import register_if_enabled

from web.english_y2_verified_workbook_runtime import install as install_english_y2_workbook

# Preserve all existing handlers; add only verified Year 2 Workbook availability.
ENGLISH_Y2_WORKBOOK_BRIDGE_ACTIVE = install_english_y2_workbook(telegram_runtime)

from web.english_y4_standalone_runtime import install as install_english_y4_standalone
ENGLISH_Y4_STANDALONE_ACTIVE = install_english_y4_standalone(telegram_runtime)

# Year 6 standalone RPH is applied at the existing Word/PDF row renderer.
# The original credit gate, lesson navigation and fallback remain unchanged.
try:
    from web.english_y6_standalone_runtime import install as install_english_y6_rph
    ENGLISH_Y6_RPH_2027_ACTIVE = install_english_y6_rph(telegram_runtime)
except Exception as _y6_rph_exc:
    ENGLISH_Y6_RPH_2027_ACTIVE = False
    print("English Year 6 RPH bridge unavailable:", repr(_y6_rph_exc), flush=True)


# The existing Year 4 text-only adapter does not feed Word/PDF rendering.
# Patch the final shared RPH row constructor for fixed-SOW, reviewed Year 4
# standalone lessons; preserve draft teacher-choice lessons and all quotas.
try:
    from web.english_y4_standalone_runtime import install_rows as install_english_y4_rows
    ENGLISH_Y4_WORD_PDF_ROWS_ACTIVE = install_english_y4_rows(telegram_runtime)
except Exception as _y4_rows_exc:
    ENGLISH_Y4_WORD_PDF_ROWS_ACTIVE = False
    print("English Year 4 Word/PDF row bridge unavailable:", repr(_y4_rows_exc), flush=True)


# Compact the Year 6 English RPH Word layout only after source creation.
# The 8pt A4 layout passed eight representative offline Word->PDF samples;
# content, existing PDF generator, user DB and quota accounting are untouched.
try:
    from web.english_y6_word_a4_runtime import install as install_english_y6_word_a4
    ENGLISH_Y6_WORD_A4_ACTIVE = install_english_y6_word_a4(telegram_runtime)
except Exception as _y6_word_a4_exc:
    ENGLISH_Y6_WORD_A4_ACTIVE = False
    print("English Year 6 Word A4 bridge unavailable:", repr(_y6_word_a4_exc), flush=True)


# Scoped Word-only A4 repair for five verified English Year 2 overflow Lessons.
# All 160 sources were inspected offline; only L2,3,12,13,14 need 8pt margins.
# No PDF-native, DB, quota, callback, other subject, or Year 5 changes.
try:
    from web.english_y2_word_a4_runtime import install as install_english_y2_word_a4
    ENGLISH_Y2_WORD_A4_ACTIVE = install_english_y2_word_a4(telegram_runtime)
except Exception as _y2_word_a4_exc:
    ENGLISH_Y2_WORD_A4_ACTIVE = False
    print("English Year 2 Word A4 bridge unavailable:", repr(_y2_word_a4_exc), flush=True)


# English Year 5 is a DRAF staging source. Keep production disabled until
# printed-page/audio/A4 and teacher QA are approved. Opt-in only for controlled tests.
try:
    from web.english_y5_standalone_runtime import install as install_english_y5_rph
    ENGLISH_Y5_DRAFT_RPH_ACTIVE = install_english_y5_rph(telegram_runtime)
except Exception as _y5_rph_exc:
    ENGLISH_Y5_DRAFT_RPH_ACTIVE = False
    print("English Year 5 gated RPH bridge unavailable:", repr(_y5_rph_exc), flush=True)


app = telegram_runtime.app


def active_master_database():
    if not getattr(telegram_runtime, "CIKGULAJU_DB_V2600_ACTIVE", False):
        return None
    return getattr(telegram_runtime, "DB_PATH", None)


register_if_enabled(app, active_master_database)

# RPT English 2027 PDF download: install after all Telegram callback wrappers.
# This does not alter app.py, RPH generation, DB state or quota debits.
try:
    from rpt_2027.english.telegram_downloads import install as install_english_rpt_2027
    ENGLISH_RPT_2027_TELEGRAM_ACTIVE = install_english_rpt_2027(vars(telegram_runtime))
except Exception as _rpt_2027_exc:
    ENGLISH_RPT_2027_TELEGRAM_ACTIVE = False
    print("English RPT 2027 Telegram bridge unavailable:", repr(_rpt_2027_exc), flush=True)


# Temporary Matematik v28 RPT PDFs are served only from a private, local
# server directory after the same paid entitlement checks. Never fetch an
# unshared Drive URL directly or expose a public file link.
try:
    from rpt_2027.matematik.telegram_downloads import install as install_math_rpt_2027
    MATEMATIK_RPT_2027_TELEGRAM_ACTIVE = install_math_rpt_2027(vars(telegram_runtime))
except Exception as _math_rpt_2027_exc:
    MATEMATIK_RPT_2027_TELEGRAM_ACTIVE = False
    print("Matematik RPT 2027 Telegram bridge unavailable:", repr(_math_rpt_2027_exc), flush=True)


# PJPK Tahun 2–6: admin-only source preview. Feature flag OFF by default.
# The existing selection -> class -> credit -> Word/PDF route is reused;
# no database, payment, production readiness or global subject is changed.
try:
    from web.pjpk_2027_preview_runtime import install as install_pjpk_preview
    PJPK_2027_PREVIEW_INSTALLED = install_pjpk_preview(vars(telegram_runtime))
except Exception as _pjpk_preview_exc:
    PJPK_2027_PREVIEW_INSTALLED = False
    print("PJPK 2027 preview disabled:", repr(_pjpk_preview_exc), flush=True)
