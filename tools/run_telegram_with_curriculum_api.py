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


# Offline A4 parity fix for only the new Year4 (11) and Year5 (151)
# provisional Word previews. The nine Year5 teacher-choice proposals retain
# their already deployed Word A4 handler. No changes to native PDF, credits,
# database, or other years/subjects.
try:
    from web.english_y4_y5_draft_word_a4_runtime import install as install_y4_y5_draft_word_a4
    ENGLISH_Y4_Y5_DRAFT_WORD_A4_ACTIVE = install_y4_y5_draft_word_a4(telegram_runtime)
except Exception as _y4_y5_word_exc:
    ENGLISH_Y4_Y5_DRAFT_WORD_A4_ACTIVE = False
    print("English Year 4/5 draft Word A4 unavailable:", repr(_y4_y5_word_exc), flush=True)



# The AST-locked 149-Lesson Year4 Word audit found only Lesson 002 needs
# compact A4 margins. Keep the 148 other reviewed Year4 lessons unchanged.
# Native PDF, other subjects, the user DB and all quota checks are untouched.
try:
    from web.english_y4_l002_word_a4_runtime import install as install_english_y4_l002_a4
    ENGLISH_Y4_L002_WORD_A4_ACTIVE = install_english_y4_l002_a4(telegram_runtime)
except Exception as _y4_l002_a4_exc:
    ENGLISH_Y4_L002_WORD_A4_ACTIVE = False
    print("English Y4 Lesson 002 Word A4 unavailable:", repr(_y4_l002_a4_exc), flush=True)


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


# PJPK Year 2-6 DRAF RPH: available to regular Telegram users via the same
# existing class/date, RPH Word/PDF, subscription and free-credit gates.
# Source is the 339-row RPT 2027 manifest; all rows remain DRAF/not READY.
# This bridge performs no database, user, subscription or quota mutation.
try:
    from web.pjpk_2027_preview_runtime import install as install_pjpk_rph_2027
    PJPK_2027_RPH_INSTALLED = install_pjpk_rph_2027(
        vars(telegram_runtime), enabled=True)
except Exception as _pjpk_rph_exc:
    PJPK_2027_RPH_INSTALLED = False
    print("PJPK DRAF RPH bridge unavailable:", repr(_pjpk_rph_exc), flush=True)


# PJPK RPT 2027 (PDF DRAF) — read-only paid-gated route.
# Installed after English/BM/Math/PI so all other callbacks remain intact.
try:
    from rpt_2027.pjpk.telegram_downloads import install as install_pjpk_rpt_2027
    PJPK_RPT_2027_TELEGRAM_ACTIVE = install_pjpk_rpt_2027(vars(telegram_runtime))
except Exception as _pjpk_rpt_2027_exc:
    PJPK_RPT_2027_TELEGRAM_ACTIVE = False
    print("PJPK RPT 2027 download route unavailable:", repr(_pjpk_rpt_2027_exc), flush=True)

# Opt-out 80%-ready Moral source bridge for the existing native Word/PDF RPH.
# Only Moral Years 2-6 / correctly mapped PdP rows; no DB or quota mutations.
try:
    from web.pendidikan_moral_80_runtime import install as install_moral_80
    MORAL_80_RPH_ACTIVE = install_moral_80(telegram_runtime)
except Exception as _moral80_exc:
    MORAL_80_RPH_ACTIVE = False
    print("Moral 80 RPH bridge unavailable:", repr(_moral80_exc), flush=True)


# 2027 Moral proposed RPT PDF generated on demand from the staged CSV sequence.
try:
    from rpt_2027.pendidikan_moral.telegram_downloads import install as install_moral_rpt_2027
    MORAL_RPT_2027_TELEGRAM_ACTIVE = install_moral_rpt_2027(vars(telegram_runtime))
except Exception as _moralrpt_exc:
    MORAL_RPT_2027_TELEGRAM_ACTIVE = False
    print("Moral RPT 2027 download route unavailable:", repr(_moralrpt_exc), flush=True)

# Paid Moral 2027 full 96-session group A/B downloads, plus supplementary
# 54-session editable Word/PDF packs. A narrow callback wrapper; no DB writes.
try:
    from rpt_2027.pendidikan_moral.complete_96_downloads import install as install_moral_96
    MORAL_96_DOWNLOADS_ACTIVE = install_moral_96(vars(telegram_runtime))
except Exception as _moral96_exc:
    MORAL_96_DOWNLOADS_ACTIVE = False
    print("Moral 96 downloads unavailable:", repr(_moral96_exc), flush=True)

# Invite-only referral navigation, installed last so all existing menu features
# remain intact. Visible only to users previously approved by /refadd.
try:
    from web.private_referral_menu_runtime import install as install_private_referral_buttons
    PRIVATE_REFERRAL_MENU_BUTTONS_ACTIVE = install_private_referral_buttons(telegram_runtime)
except Exception as _private_referral_menu_exc:
    PRIVATE_REFERRAL_MENU_BUTTONS_ACTIVE = False
    print("Private referral menu integration unavailable:",
          type(_private_referral_menu_exc).__name__, flush=True)

# Read-only admin referral points; the last wrapper on callback and admin_panel.
# Only _is_admin() identities can access this data; no payment or credit writes.
try:
    from web.private_referral_admin_runtime import install as install_private_referral_admin
    PRIVATE_REFERRAL_ADMIN_POINTS_ACTIVE = install_private_referral_admin(telegram_runtime)
except Exception as _ref_admin_exc:
    PRIVATE_REFERRAL_ADMIN_POINTS_ACTIVE = False
    print("Private referral admin report unavailable:",
          type(_ref_admin_exc).__name__, flush=True)

# English Year 4 Lesson 30: fail closed on a proven source discrepancy.
# Original app.py v25.257/v25.258/v25.259 maps L030 to CD2 Track29,
# while printed TB p39 identifies CD1 Track29 for SB p20 Activity 2.
# Until the spoken content and exact Telegram delivery are independently
# verified, hide only the L030 media option and reject stale callback sends.
# Install last; all other lesson audio, Word/PDF, quotas and database stay intact.
try:
    from web.english_y4_l030_audio_guard import install as install_y4_l030_audio_guard
    ENGLISH_Y4_L030_AUDIO_GUARD_ACTIVE = install_y4_l030_audio_guard(telegram_runtime)
except Exception as _y4_l030_audio_exc:
    ENGLISH_Y4_L030_AUDIO_GUARD_ACTIVE = False
    print("English Y4 L030 audio source safety guard unavailable:",
          type(_y4_l030_audio_exc).__name__, flush=True)

# Year4 Get Smart Plus4: 24 legacy WMA files came from the
# 'Super Minds 1 Audio Unzipped' folder. Block only 19 affected
# Year4 Lessons' media buttons and stale callbacks until the correct
# TB-verified tracks have been tested. Preserve RPH Word/PDF, all other
# Years/subjects, teacher data, billing, credits and subscriptions.
# Install after the existing Lesson30 audio guard so both protections hold.
try:
    from web.english_y4_wrong_book_audio_hold_20261105 import install as install_y4_wrong_book_audio_hold
    ENGLISH_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE = install_y4_wrong_book_audio_hold(telegram_runtime)
except Exception as _y4_wrong_book_exc:
    ENGLISH_Y4_WRONG_BOOK_AUDIO_HOLD_ACTIVE = False
    print("English Year4 wrong-textbook audio hold unavailable:",
          type(_y4_wrong_book_exc).__name__, flush=True)



# Durable teacher/user records: payment IDs, statuses, admin approvals, Telegram
# names and user feedback are stored in Supabase when explicitly enabled.
# Installed after all existing Telegram bridges so every callback reads the
# latest runtime handlers. NEVER auto-enable without the additive migration.
try:
    from web.supabase_user_payment_runtime import install as install_user_payment_store
    DURABLE_USER_PAYMENT_STORE_ACTIVE = bool(install_user_payment_store(telegram_runtime))
except Exception as _durable_payment_exc:
    DURABLE_USER_PAYMENT_STORE_ACTIVE = False
    print("Durable user payment store installation failed:",
          type(_durable_payment_exc).__name__,flush=True)

try:
    from web.supabase_user_feedback_runtime import install as install_user_feedback_store
    DURABLE_USER_FEEDBACK_STORE_ACTIVE = bool(install_user_feedback_store(telegram_runtime))
except Exception as _durable_feedback_exc:
    DURABLE_USER_FEEDBACK_STORE_ACTIVE = False
    print("Durable user feedback store installation failed:",
          type(_durable_feedback_exc).__name__,flush=True)

# Read-only admin receipt preview and MYT submit times. The Supabase queue must
# already be active; never fall back to potentially stale local SQLite receipts.
try:
    from web.payment_receipt_admin_runtime import install as install_payment_receipt_admin
    PAYMENT_RECEIPT_ADMIN_ACTIVE = bool(
        DURABLE_USER_PAYMENT_STORE_ACTIVE and install_payment_receipt_admin(telegram_runtime))
except Exception as _receipt_view_exc:
    PAYMENT_RECEIPT_ADMIN_ACTIVE = False
    print("Admin payment receipt view unavailable:", type(_receipt_view_exc).__name__, flush=True)

# The Telegram payment QR is only a draft intent. A real pending row is
# created on the customer's verified photo/PDF webhook message, not on QR open.
# Install after the durable Supabase queue so this never writes to local SQLite.
try:
    from web.payment_record_on_proof_runtime import install as install_proof_first_payment
    PROOF_FIRST_PAYMENT_ACTIVE = bool(
        DURABLE_USER_PAYMENT_STORE_ACTIVE
        and install_proof_first_payment(telegram_runtime))
except Exception as _proof_first_exc:
    PROOF_FIRST_PAYMENT_ACTIVE = False
    print("Proof-first payment feature unavailable:",
          type(_proof_first_exc).__name__, flush=True)


# Public Telegram manual: add one main-menu button and send a PDF to any user
# without decrementing RPH credits or requiring payment. Install last so
# existing private-referral navigation is preserved in the final keyboard.
try:
    from web.manual_pengguna_telegram import install as install_user_manual
    USER_MANUAL_MENU_ACTIVE = bool(install_user_manual(telegram_runtime))
except Exception as _manual_exc:
    USER_MANUAL_MENU_ACTIVE = False
    print("Public user manual menu unavailable:",
          type(_manual_exc).__name__, flush=True)


# Owner-approved provisional PSV 2027 RPH access (Years 2–6, 210 PdP).
# This uses existing Telegram subject -> numbered PdP -> class/date -> PDF/Word
# and original subscription/credit checks. Source RPH remains DRAF, the formal
# 210-signoff release bridge stays fail-closed, and no user/DB fields are changed.
# Emergency opt-out: CIKGULAJU_PSV_PROVISIONAL_ENABLED=0.
try:
    from web.psv_2027_provisional_runtime import install as install_psv_provisional
    PSV_2027_PROVISIONAL_RPH_ACTIVE = bool(install_psv_provisional(vars(telegram_runtime)))
except Exception as _psv_provisional_exc:
    PSV_2027_PROVISIONAL_RPH_ACTIVE = False
    print("PSV provisional RPH route unavailable:",
          type(_psv_provisional_exc).__name__, flush=True)

# Sejarah Years 4–6 user-facing DRAF proposals. Uses existing Telegram
# class/date, native Word/PDF and quota checks. Source and approval flags are
# immutable; switch off instantly with CIKGULAJU_SEJARAH_2027_USER_ENABLED=0.
try:
    from web.sejarah_2027_user_runtime import install as install_sejarah_2027
    SEJARAH_2027_USER_BRIDGE_ACTIVE = bool(
        install_sejarah_2027(vars(telegram_runtime)))
except Exception as _sej27_exc:
    SEJARAH_2027_USER_BRIDGE_ACTIVE = False
    print("Sejarah Year 4-6 user bridge unavailable:",
          type(_sej27_exc).__name__, flush=True)


# RBT Year 4-6 source-bound Telegram menu, opt-in DRAF preview only.
# Disabled unless CIKGULAJU_RBT_2027_DRAFT_USER_ENABLED=1.
try:
    from web.rbt_2027_user_runtime import install as install_rbt_2027
    RBT_2027_DRAFT_USER_BRIDGE_ACTIVE = bool(
        install_rbt_2027(vars(telegram_runtime)))
except Exception as _rbt27_exc:
    RBT_2027_DRAFT_USER_BRIDGE_ACTIVE = False
    print("RBT draft Telegram bridge unavailable:",
          type(_rbt27_exc).__name__, flush=True)

# RBT RPT 2027: source-matched landscape PDF, paid-only and draft-labelled.
# Wraps only rbt27rpt callbacks; preserves all unrelated RPT/subscription flows.
try:
    from rpt_2027.rbt.telegram_downloads import install as install_rbt_rpt
    RBT_2027_RPT_DRAFT_INSTALLED = bool(
        install_rbt_rpt(vars(telegram_runtime)))
except Exception as _rbt_rpt_exc:
    RBT_2027_RPT_DRAFT_INSTALLED = False
    print("RBT 2027 RPT route unavailable:",type(_rbt_rpt_exc).__name__,flush=True)

# Authenticated Web -> native Telegram RPH document generation.
# Disabled unless CIKGULAJU_WEB_NATIVE_RPH_ENABLED=1; fail closed.
# This does not alter Telegram webhook/callbacks, DB, trials, or payments.
try:
    from web.native_rph_telegram_api import create_native_rph_blueprint
    telegram_runtime.app.register_blueprint(
        create_native_rph_blueprint(telegram_runtime))
    TELEGRAM_NATIVE_WEB_RPH_REGISTERED = True
except Exception as _native_rph_error:
    TELEGRAM_NATIVE_WEB_RPH_REGISTERED = False
    print("Native Web RPH route unavailable:",
          type(_native_rph_error).__name__, flush=True)


# Web BM / Pendidikan Islam RPH directly from verified Telegram master RPT.
# Same native Word/PDF renderer and source DB, never a Web-side RPH copy.
try:
    from web.telegram_verified_rpt_rph_bridge import create_native_db_rph_blueprint
    telegram_runtime.app.register_blueprint(
        create_native_db_rph_blueprint(telegram_runtime))
    TELEGRAM_NATIVE_DB_RPH_BRIDGE_REGISTERED = True
except Exception as _native_db_rph_exc:
    TELEGRAM_NATIVE_DB_RPH_BRIDGE_REGISTERED = False
    print("Native verified RPT RPH bridge unavailable:",
          type(_native_db_rph_exc).__name__, flush=True)


# BM Web: resolve the actual Telegram verified_pdp_sequence source, not
# rpt_entries, then reuse the native Telegram Word/PDF generator.
# Exact selection is re-resolved on each request; no DB changes.
try:
    from web.telegram_native_bm_sequence_rph_bridge import (
        create_native_bm_rph_blueprint,
    )
    telegram_runtime.app.register_blueprint(
        create_native_bm_rph_blueprint(telegram_runtime))
    TELEGRAM_NATIVE_BM_SEQUENCE_RPH_REGISTERED = True
except Exception as _native_bm_sequence_exc:
    TELEGRAM_NATIVE_BM_SEQUENCE_RPH_REGISTERED = False
    print("Native BM sequence RPH unavailable:",
          type(_native_bm_sequence_exc).__name__, flush=True)


# Year 5 Sains source is installed only for explicit *isolated staging*
# validation. Live Render services are blocked by the module's safety gate.
# Never alter production source, quota, user or DB by importing this file.
import os as _sains_review_env
if _sains_review_env.environ.get("CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW") == "1":
    from web.sains_y5_83_staging_shared_runtime_20261108 import (
        install as _install_sains_y5_83_review,
    )
    SAINS_Y5_83_INTERNAL_REVIEW_ACTIVE = _install_sains_y5_83_review(telegram_runtime)
else:
    SAINS_Y5_83_INTERNAL_REVIEW_ACTIVE = False


# Sains T2–T6: explicitly isolated staging reviewer for 342 authored PdP.
# Uses only repository-committed DSKP + activity banks at runtime, never
# transient CI build outputs. No new RPH can be published by this switch
# on the real Telegram/Web Render production services.
if _sains_review_env.environ.get("CIKGULAJU_SAINS_342_INTERNAL_REVIEW") == "1":
    from web.sains_342_native_staging_source_20261108 import (
        install as _install_sains_342_review,
    )
    SAINS_342_INTERNAL_REVIEW_ACTIVE = _install_sains_342_review(telegram_runtime)
else:
    SAINS_342_INTERNAL_REVIEW_ACTIVE = False


# Sains / Matematik: Web units and PdP selections use Telegram's exact
# grouped verified_pdp_sequence reader, not misleading weekly RPT row IDs.
try:
    from web.telegram_verified_sequence_rph_bridge import (
        create_native_sequence_rph_blueprint,
    )
    telegram_runtime.app.register_blueprint(
        create_native_sequence_rph_blueprint(telegram_runtime))
    TELEGRAM_NATIVE_SEQUENCE_RPH_REGISTERED = True
except Exception as _native_sequence_exc:
    TELEGRAM_NATIVE_SEQUENCE_RPH_REGISTERED = False
    print("Native sequence RPH unavailable:",
          type(_native_sequence_exc).__name__, flush=True)


# Sejarah: register private source reader for the dedicated Web client.
try:
    from web.sejarah_2027_native_api import create_sejarah_2027_native_blueprint
    telegram_runtime.app.register_blueprint(
        create_sejarah_2027_native_blueprint(telegram_runtime))
    SEJARAH_2027_WEB_READER_REGISTERED = True
except Exception as exc:
    SEJARAH_2027_WEB_READER_REGISTERED = False
    print("Sejarah Web reader unavailable:", type(exc).__name__, flush=True)

# Bahasa Arab + Pendidikan Muzik DRAF: isolate staged source behind the
# existing private service authentication. No Telegram callback, DB, audio,
# account or payment changes. Both subjects remain DRAF for teacher review.
try:
    from web.telegram_provisional_arab_music_api import (
        create_provisional_subjects_blueprint,
    )
    telegram_runtime.app.register_blueprint(
        create_provisional_subjects_blueprint(telegram_runtime))
    OTHER_SUBJECTS_DRAFT_READER_REGISTERED = True
except Exception as exc:
    OTHER_SUBJECTS_DRAFT_READER_REGISTERED = False
    print("Arabic/Music DRAF source unavailable:",
          type(exc).__name__, flush=True)


# English: authenticated workbook material from the original verified
# Lesson -> Workbook page map. Extract only the mapped PDF page(s).
try:
    from web.telegram_english_workbook_api_20261106 import create_english_workbook_blueprint
    telegram_runtime.app.register_blueprint(create_english_workbook_blueprint(telegram_runtime))
    ENGLISH_EXTRA_WORKBOOK_SOURCE_REGISTERED = True
except Exception as exc:
    ENGLISH_EXTRA_WORKBOOK_SOURCE_REGISTERED = False
    print("English extra workbook route unavailable:", type(exc).__name__, flush=True)


# RBT: Web uses the same Telegram curriculum and native Word/PDF engine.
# Token-authenticated, opt-in, no database, subscription or quota changes.
try:
    from web.rbt_2027_native_api import create_rbt_2027_native_blueprint
    telegram_runtime.app.register_blueprint(
        create_rbt_2027_native_blueprint(telegram_runtime))
    RBT_2027_WEB_READER_REGISTERED = True
except Exception as _rbt_reader_exc:
    RBT_2027_WEB_READER_REGISTERED = False
    print("RBT authenticated Web API unavailable:",
          type(_rbt_reader_exc).__name__, flush=True)

# Private source-matched RPT school covers for authenticated Web users. Web
# checks account entitlement; Telegram re-checks exact PDF bytes before it
# inserts the logo. The bot's menus, RPH, sources, and credits stay untouched.
try:
    from web.native_rpt_telegram_api import create_private_rpt_blueprint
    telegram_runtime.app.register_blueprint(create_private_rpt_blueprint())
    TELEGRAM_PRIVATE_RPT_COVER_REGISTERED = True
except Exception as _private_rpt_error:
    TELEGRAM_PRIVATE_RPT_COVER_REGISTERED = False
    print("Private RPT school cover unavailable:",
          type(_private_rpt_error).__name__, flush=True)


# Authenticated read-only QR and plan catalog for the independent Web payment
# screen. The payment/approval logic remains the original proof-first Supabase
# queue; this adapter NEVER creates pending records or sends receipts.
try:
    from web.telegram_payment_source import create_web_payment_source
    telegram_runtime.app.register_blueprint(
        create_web_payment_source(telegram_runtime))
    TELEGRAM_WEB_PAYMENT_SOURCE_REGISTERED = True
except Exception as _web_payment_catalog_error:
    TELEGRAM_WEB_PAYMENT_SOURCE_REGISTERED = False
    print("Web payment source unavailable:",
          type(_web_payment_catalog_error).__name__, flush=True)

# Private Web -> Telegram receipt notification. Registers only after the
# durable Supabase payment queue and admin receipt callbacks are ready.
# No notification occurs until a saved Pending proof is verified by its ID.
try:
    from web.telegram_web_receipt_admin_notification import (
        create_web_receipt_admin_notification,
    )
    telegram_runtime.app.register_blueprint(
        create_web_receipt_admin_notification(telegram_runtime))
    TELEGRAM_WEB_RECEIPT_REVIEW_NOTICE_REGISTERED = True
except Exception as _web_receipt_notice_exc:
    TELEGRAM_WEB_RECEIPT_REVIEW_NOTICE_REGISTERED = False
    print("Web receipt admin notification unavailable:",
          type(_web_receipt_notice_exc).__name__, flush=True)


# Optional verified-source API for the 59 DRAF Aktiviti Khas records.
# The source and labels stay separate from syllabus-based Unit/Lesson/PdP.
# Only registers when the explicit Special Activity flag and existing private
# native Web-to-Telegram token are configured; fail closed otherwise.
try:
    from web.telegram_special_activity_api import register_if_enabled as register_special_rph
    SPECIAL_ACTIVITY_2027_PRIVATE_API_ACTIVE = bool(
        register_special_rph(telegram_runtime.app))
except Exception as _special_activity_api_exc:
    SPECIAL_ACTIVITY_2027_PRIVATE_API_ACTIVE = False
    print("Special Activity RPH API unavailable:",
          type(_special_activity_api_exc).__name__, flush=True)


# Authenticated Web referral registration notice to Telegram admin. Does not
# create users, alter payment status or change existing signup notifications.
try:
    from web.telegram_web_referral_admin_notice import create_web_referral_signup_notice
    telegram_runtime.app.register_blueprint(
        create_web_referral_signup_notice(telegram_runtime))
    TELEGRAM_WEB_REFERRAL_SIGNUP_NOTICE_REGISTERED = True
except Exception as _web_referral_admin_exc:
    TELEGRAM_WEB_REFERRAL_SIGNUP_NOTICE_REGISTERED = False
    print("Web referral admin notice unavailable:",
          type(_web_referral_admin_exc).__name__, flush=True)


# Direct Web registration (Telegram Login Widget) admin notice. Uses
# Supabase authoritative user ID and a durable once-only notification marker.
try:
    from web.telegram_web_direct_signup_admin_notice import (
        create_web_direct_signup_admin_notice,
    )
    telegram_runtime.app.register_blueprint(
        create_web_direct_signup_admin_notice(telegram_runtime))
    TELEGRAM_WEB_DIRECT_SIGNUP_NOTICE_REGISTERED = True
except Exception as _web_direct_notice_exc:
    TELEGRAM_WEB_DIRECT_SIGNUP_NOTICE_REGISTERED = False
    print("Web direct signup admin notice unavailable:",
          type(_web_direct_notice_exc).__name__, flush=True)


# Add the Web URL after all existing Telegram menu wrappers. Preserve
# private referral access, manual PDF, payment and other callback handlers.
try:
    from web.web_link_telegram import install as install_web_link
    TELEGRAM_WEB_LINK_MENU_ACTIVE = bool(install_web_link(telegram_runtime))
except Exception as _web_menu_error:
    TELEGRAM_WEB_LINK_MENU_ACTIVE = False
    print("Telegram Web menu unavailable:", type(_web_menu_error).__name__, flush=True)

# Registration intentionally last. DURABLE_USER_PAYMENT_STORE_ACTIVE is
# only available after the Supabase user-record bridge above; registering any
# earlier caused a startup NameError and hid the broadcast button.
# Admin-only Web launch announcement, installed after referral admin's
# panel edit to merge both buttons into the final Telegram keyboard. It cannot
# send anything at deployment or when Panel Admin is opened: admin must preview
# and explicitly confirm first. Each attempted recipient is logged in Supabase.
try:
    from web.admin_web_launch_broadcast import install as install_web_announcement
    TELEGRAM_WEB_BROADCAST_READY = bool(
        DURABLE_USER_PAYMENT_STORE_ACTIVE
        and install_web_announcement(
            telegram_runtime,
            preserve_referral=PRIVATE_REFERRAL_ADMIN_POINTS_ACTIVE))
except Exception as _web_broadcast_exc:
    TELEGRAM_WEB_BROADCAST_READY = False
    print("Web launch admin broadcast unavailable:",
          type(_web_broadcast_exc).__name__, flush=True)


# Read-only production self-check of CURRENT Science DB RPH readiness.
# This only samples one existing PdP per year, logs presence of source and
# Word/PDF field builder, and never creates documents or touches user credits.
# All 342 newly authored Science RPH remain DRAF/HOLD until per-PdP signoff.
try:
    from tools.sains_native_runtime_readiness_probe_20261108 import (
        log_readiness as _log_sains_native_readiness,
    )
    SAINS_NATIVE_READINESS_REPORT = _log_sains_native_readiness(telegram_runtime)
except Exception as _sains_readiness_diagnostic_exc:
    SAINS_NATIVE_READINESS_REPORT = None
    print("Sains native readiness diagnostic unavailable:",
          type(_sains_readiness_diagnostic_exc).__name__, flush=True)


# Final output-only RPH typography: ensure Aktiviti 1/2/3/4 headings are
# consistently bold in Word and PDF (including colon variants).
# Runs after native subject adapters so no source RPH, SK/SP or DB is changed.
try:
    from web.rph_activity_headings_typography import install as install_rph_activity_heading_bold
    RPH_ACTIVITY_HEADING_BOLD_INSTALLED = bool(
        install_rph_activity_heading_bold(telegram_runtime))
except Exception as _rph_activity_heading_exc:
    RPH_ACTIVITY_HEADING_BOLD_INSTALLED = False
    print("RPH typography unavailable:",
          type(_rph_activity_heading_exc).__name__, flush=True)



# Admin-controlled, one-shot internal validation of actual Sains native Word/PDF.
# Disabled by default. Uses synthetic metadata and the exact registered
# private Telegram -> Web sequence API; no user login, credits or DB mutation.
# Runs only when CIKGULAJU_SAINS_NATIVE_REAL_DOCS_SMOKE=1 and leaves all 342
# new authoring drafts on HOLD. Reports each year without leaking content.
try:
    from tools.sains_native_internal_real_documents_smoke_20261108 import (
        log_when_enabled as _sains_native_real_docs_smoke,
    )
    SAINS_NATIVE_REAL_DOCS_SMOKE_RESULT = _sains_native_real_docs_smoke(telegram_runtime)
except Exception as _sains_real_docs_smoke_error:
    SAINS_NATIVE_REAL_DOCS_SMOKE_RESULT = None
    print("CIKGULAJU_SAINS_NATIVE_REAL_DOCS_SMOKE_UNAVAILABLE",
          type(_sains_real_docs_smoke_error).__name__,flush=True)


# Final Matematik SK presentation correction for native Telegram/Web Word/PDF.
# The grouped curriculum source can repeat an SK code in both code and text;
# remove only adjacent identical display prefixes (e.g. "4.4 4.4 Darab wang").
# No SK/SP mapping, objectives, durations, downloads, credits or DB are changed.
try:
    from web.math_rph_sk_display_fix_20261110 import install as install_math_sk_display_fix
    MATEMATIK_SK_DISPLAY_FIX_ACTIVE = bool(install_math_sk_display_fix(telegram_runtime))
except Exception as _math_sk_display_exc:
    MATEMATIK_SK_DISPLAY_FIX_ACTIVE = False
    print("Matematik SK label formatting unavailable:",
          type(_math_sk_display_exc).__name__, flush=True)


# User-visible Telegram parity for the existing Web Special Activities catalogue.
# Installs AFTER previous menu/referral/credit adapters; only prefixes "ak26:"
# callbacks. Shares the same immutable 59 DRAFT_REVIEW records, digest, Word/PDF.
# No modifications to curriculum DB, ordinary Lesson/PdP selection, or RPT.
try:
    from web.telegram_special_activity_menu import install as install_special_rph_menu
    TELEGRAM_SPECIAL_ACTIVITY_MENU_ACTIVE = bool(install_special_rph_menu(telegram_runtime))
except Exception as _special_menu_error:
    TELEGRAM_SPECIAL_ACTIVITY_MENU_ACTIVE = False
    print("Telegram Special Activity menu unavailable:",
          type(_special_menu_error).__name__, flush=True)

# Restore Telegram RPH Hari Ini from teacher-entered weekly timetable.
# Keep all existing verified curriculum, delivery, trial and progress gates.
# AI photo/PDF timetable reading is intentionally disabled.
try:
    from web.telegram_rph_hari_ini_manual_20261110 import install as install_daily_manual
    TELEGRAM_DAILY_MANUAL_ACTIVE = bool(install_daily_manual(telegram_runtime))
except Exception as _daily_manual_error:
    TELEGRAM_DAILY_MANUAL_ACTIVE = False
    print("Telegram daily manual timetable unavailable:",
          type(_daily_manual_error).__name__, flush=True)

# UI-only two-choice entry in "Sediakan RPH".
# RPH Harian retains choose_grade -> existing Lesson/PdP -> matsubmit2528;
# RPH Aktiviti Khas opens existing ak26:home catalogue. No route rewrites.
try:
    from web.telegram_rph_entry_choices_20261110 import install as install_rph_entry_choices
    TELEGRAM_RPH_ENTRY_CHOICES_ACTIVE = bool(install_rph_entry_choices(telegram_runtime))
except Exception as _rph_entry_choices_error:
    TELEGRAM_RPH_ENTRY_CHOICES_ACTIVE = False
    print("Telegram RPH entry choices unavailable:",
          type(_rph_entry_choices_error).__name__, flush=True)
