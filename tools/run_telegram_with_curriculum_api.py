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


# Y2/Y3 source activities already enter native _rph_rows via app.py.
# The older adapters leave the English Main/Complementary Word/PDF cells
# unchanged; fill these cells only if header and official SOW pairs match.
# No Year 1 path is touched and no user credit/DB change is made.
try:
    from web.english_y2_y3_standard_runtime import install as install_english_y2_y3_sow_fields
    ENGLISH_Y2_Y3_SOW_WORD_PDF_ACTIVE = install_english_y2_y3_sow_fields(telegram_runtime)
except Exception as _y2_y3_sow_exc:
    ENGLISH_Y2_Y3_SOW_WORD_PDF_ACTIVE = False
    print("English Year 2/3 SOW Word/PDF fields unavailable:", repr(_y2_y3_sow_exc), flush=True)


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


# Nine Year 5 teacher-choice Lessons: present clearly marked CikguLaju DRAFT
# suggestions in native Word/PDF. The SOW prescribes no fixed CS/LS for
# these Lessons; teachers must choose the DSKP standards before official use.
# Separate from the existing 151 fixed-standard Year 5 release gate: none
# of those drafts is promoted or unlocked here. No DB/credit changes.
try:
    from web.english_y5_teacher_choice_runtime import install as install_english_y5_choices
    ENGLISH_Y5_TEACHER_CHOICE_PROPOSALS_ACTIVE = install_english_y5_choices(telegram_runtime)
except Exception as _y5_choices_exc:
    ENGLISH_Y5_TEACHER_CHOICE_PROPOSALS_ACTIVE = False
    print("English Year 5 choice proposals unavailable:", repr(_y5_choices_exc), flush=True)


# Apply the tested text-preserving 8pt Word A4 compact layout only to the
# nine English Year 5 teacher-choice DRAFT proposals. Native PDF and all
# other years/subjects retain their existing generator and layout.
try:
    from web.english_y5_choice_word_a4_runtime import install as install_y5_choice_word_a4
    ENGLISH_Y5_TEACHER_CHOICE_WORD_A4_ACTIVE = install_y5_choice_word_a4(telegram_runtime)
except Exception as _y5_choice_a4_exc:
    ENGLISH_Y5_TEACHER_CHOICE_WORD_A4_ACTIVE = False
    print("English Year 5 choice Word A4 unavailable:", repr(_y5_choice_a4_exc), flush=True)



# Year 4's 149 provisionally reviewed fixed-SOW lessons are preserved.
# The other ten teacher-choice lessons and L30 audio-conflict lesson are
# now available ONLY as explicitly labelled DRAF previews. No invented SPs.
try:
    from web.english_y4_pending_draft_preview_runtime import install as install_y4_pending_drafts
    ENGLISH_Y4_PENDING_DRAFT_PREVIEW_ACTIVE = install_y4_pending_drafts(telegram_runtime)
except Exception as _y4_pending_exc:
    ENGLISH_Y4_PENDING_DRAFT_PREVIEW_ACTIVE = False
    print("English Year 4 pending draft preview unavailable:", repr(_y4_pending_exc), flush=True)


# Year 5's other 151 fixed SOW lesson plans already parse and match source
# standards but lack final content/audio/A4/teacher sign-off. Show these as
# clearly labelled DRAFT suggestions in Word/PDF, not as FINAL READY; keep
# the separate byte-bound release-approval gate intact. Nine teacher-choice
# lessons remain handled by the previously installed proposal adapter.
try:
    from web.english_y5_fixed_draft_preview_runtime import install as install_y5_fixed_preview
    ENGLISH_Y5_FIXED_DRAFT_PREVIEW_ACTIVE = install_y5_fixed_preview(telegram_runtime)
except Exception as _y5_fixed_preview_exc:
    ENGLISH_Y5_FIXED_DRAFT_PREVIEW_ACTIVE = False
    print("English Year 5 fixed draft preview unavailable:", repr(_y5_fixed_preview_exc), flush=True)


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


# Bahasa Melayu 2027: RPT DRAF PDF (Tahun 2-6). Paid only, no DB edits.
# Wrapped after English menu so its new year-specific button is handled safely.
try:
    from rpt_2027.bahasa_melayu.telegram_downloads import install as install_bm_rpt_2027
    BM_RPT_2027_TELEGRAM_ACTIVE = install_bm_rpt_2027(vars(telegram_runtime))
except Exception as _bm_rpt_2027_exc:
    BM_RPT_2027_TELEGRAM_ACTIVE = False
    print("BM RPT 2027 Telegram bridge unavailable:", repr(_bm_rpt_2027_exc), flush=True)


# Temporary Matematik v28 RPT PDFs are served only from a private, local
# server directory after the same paid entitlement checks. Never fetch an
# unshared Drive URL directly or expose a public file link.
try:
    from rpt_2027.matematik.telegram_downloads import install as install_math_rpt_2027
    MATEMATIK_RPT_2027_TELEGRAM_ACTIVE = install_math_rpt_2027(vars(telegram_runtime))
except Exception as _math_rpt_2027_exc:
    MATEMATIK_RPT_2027_TELEGRAM_ACTIVE = False
    print("Matematik RPT 2027 Telegram bridge unavailable:", repr(_math_rpt_2027_exc), flush=True)


# Pendidikan Islam RPT 2027: paid-gated PDF delivery, read-only.
# The menu advertises a year only if its local PDF asset is present and valid.
try:
    from rpt_2027.pendidikan_islam.telegram_downloads import install as install_pi_rpt_2027
    PI_RPT_2027_TELEGRAM_ACTIVE = install_pi_rpt_2027(vars(telegram_runtime))
except Exception as _pi_rpt_2027_exc:
    PI_RPT_2027_TELEGRAM_ACTIVE = False
    print("Pendidikan Islam RPT 2027 Telegram bridge unavailable:", repr(_pi_rpt_2027_exc), flush=True)


# PJPK 2027 admin-only preview. OFF unless explicitly enabled on Render.
# This bridge reads standalone DRAFT files in read-only mode and intercepts only
# admin PJPK choices. Regular users continue through the existing PJPK safe gate.
# No DB changes, quota changes or READY promotions are performed.
try:
    from web.pjpk_2027_preview_runtime import install as install_pjpk_preview
    PJPK_2027_PREVIEW_INSTALLED = install_pjpk_preview(vars(telegram_runtime))
except Exception as _pjpk_preview_exc:
    PJPK_2027_PREVIEW_INSTALLED = False
    print("PJPK preview unavailable:", repr(_pjpk_preview_exc), flush=True)


# PJPK RPT 2027 (PDF DRAF) — read-only paid-gated route.
# Installed after English/BM/Math/PI so all other callbacks remain intact.
try:
    from rpt_2027.pjpk.telegram_downloads import install as install_pjpk_rpt_2027
    PJPK_RPT_2027_TELEGRAM_ACTIVE = install_pjpk_rpt_2027(vars(telegram_runtime))
except Exception as _pjpk_rpt_2027_exc:
    PJPK_RPT_2027_TELEGRAM_ACTIVE = False
    print("PJPK RPT 2027 download route unavailable:", repr(_pjpk_rpt_2027_exc), flush=True)
