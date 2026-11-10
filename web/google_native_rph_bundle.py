"""Private Google staging adapter to the same immutable Telegram RPH renderer.

NOT mounted to an HTTP endpoint. Never supplies a fake Telegram ID, bypasses
source parity, or charges a trial before BOTH native Word/PDF files complete.
The native service is configured via server-only authoritative API credentials.
"""
from datetime import date
import re

from web.native_google_rph_integrity import rendered_bundle_sha256


class NativeGoogleRPHNotReady(RuntimeError):
    pass


def _teacher_fields(teacher):
    if not isinstance(teacher, dict) or set(teacher) != {
            "class", "date", "time", "students"}:
        raise ValueError("Valid teacher class/date/time/students required")
    if not all(isinstance(item, str) for item in teacher.values()):
        raise ValueError("Invalid teacher type")
    cls, dt, tm, students = (teacher[key] for key in
                            ("class", "date", "time", "students"))
    if (len(cls) > 40 or (cls and not re.fullmatch(
            r"[\w .\-/()]+", cls, re.UNICODE))):
        raise ValueError("Invalid teacher class")
    if dt:
        if (not re.fullmatch(r"20\d\d-\d\d-\d\d", dt)
                or not 2025 <= date.fromisoformat(dt).year <= 2031):
            raise ValueError("Invalid teacher date")
    if tm:
        if (len(tm) > 13
                or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d"
                                    r"(?: - (?:[01]\d|2[0-3]):[0-5]\d)?", tm)):
            raise ValueError("Invalid teaching time")
        if " - " in tm and tm.split(" - ")[0] >= tm.split(" - ")[1]:
            raise ValueError("Inverted time range")
    if students and (not re.fullmatch(r"[1-9][0-9]{0,2}", students)
                     or int(students) > 200):
        raise ValueError("Invalid class size")
    return {key: teacher[key] for key in ("class", "date", "time", "students")}


def render_native_google_rph_bundle(year, subject, unit, lesson_token, teacher,
                                    component=None, *, native_renderer=None,
                                    preview_reader=None, fingerprint=None,
                                    layout_builder=None, y5_approval=None):
    """Return validated native files only if source fingerprint + release match.

    This internal function has NO account or quota authority. Its caller must
    independently verify signed Google account and charge with the same
    server-owned idempotency reference before returning any downloadable file.
    """
    from web.unified_rph_web import (
        SUBJECT_LABELS, verified_preview, source_records)
    from web.rph_shared_source_identity import source_fingerprint
    from web.telegram_rph_parity import build_layout
    from web.native_telegram_rph_client import (
        request_native_rph, NativeRPHUnavailable)

    if type(year) is not int or year not in range(2, 7):
        raise ValueError("Unsupported year")
    if subject not in ("ENGLISH", "MORAL", "PJPK", "PSV"):
        raise ValueError("Unsupported source subject")
    if (not isinstance(unit, str) or not 0 < len(unit) <= 300
            or not isinstance(lesson_token, str) or not 0 < len(lesson_token) <= 120
            or (subject == "PJPK" and component not in ("PJ", "PK"))
            or (subject != "PJPK" and component is not None)):
        raise ValueError("Invalid verified RPH selection")
    validated_teacher = _teacher_fields(teacher)
    read = preview_reader or verified_preview
    digest_fn = fingerprint or source_fingerprint
    build = layout_builder or build_layout
    render = native_renderer or request_native_rph

    try:
        selected = read(year, subject, unit, lesson_token, component)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise NativeGoogleRPHNotReady("RPH source not verified") from None
    if not isinstance(selected, dict) or selected.get("source") != "existing-standalone-rph":
        raise NativeGoogleRPHNotReady("Verified standalone RPH missing")
    n = selected.get("lesson")
    if type(n) is not int or n < 1:
        raise NativeGoogleRPHNotReady("Invalid lesson identity")
    if subject == "ENGLISH" and year == 5:
        if y5_approval is None:
            from web.english_y5_standalone_runtime import approved_for_telegram
            y5_approval = approved_for_telegram
        if y5_approval(n) is not True:
            raise NativeGoogleRPHNotReady("Year 5 RPH awaiting approval")
    source_digest = digest_fn(year, subject, n, component)
    if (not isinstance(source_digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", source_digest)):
        raise NativeGoogleRPHNotReady("Telegram/Web source parity unavailable")
    selected = {**selected, "teacher":validated_teacher,
                "source_digest":source_digest}
    try:
        layout = build(selected, SUBJECT_LABELS)
        if not isinstance(layout, dict) or layout.get("style") != "telegram-native-rph-v1":
            raise NativeGoogleRPHNotReady("Native RPH layout incomplete")
        selected["telegram_layout"] = layout
        # Native renderer uses an internal token and immutable source digest,
        # NOT a Telegram user's identity or quota. No local PDF fallback.
        word = render(selected, "word").getvalue()
        pdf = render(selected, "pdf").getvalue()
        bundle_hash = rendered_bundle_sha256(word, pdf)
    except (NativeRPHUnavailable, ValueError, KeyError, TypeError, OSError, AttributeError):
        raise NativeGoogleRPHNotReady("Native Word/PDF generation unavailable") from None
    return {"word": word, "pdf": pdf,
            "source_digest": source_digest,
            "document_manifest_sha256": bundle_hash,
            "subject": subject, "year": year, "lesson": n}
