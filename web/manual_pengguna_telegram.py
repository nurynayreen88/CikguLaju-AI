"""Public user manual entry in the existing CikguLaju Telegram main menu.

This is deliberately additive: no edits to the curriculum DB, payment queue,
free RPH credits, entitlements, or user records. Generates a PDF from the
versioned source when a user clicks the manual button.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

import requests


SOURCE = Path(__file__).resolve().parents[1] / "docs" / "manual_pengguna_cikgulaju_2026.txt"
BUTTON = {"text": "📖 Manual Pengguna", "callback_data": "manual_pengguna_pdf"}
_REFERRAL_BUTTON = {"text": "🎁 Referral Saya", "callback_data": "private_referral_home"}


def build_pdf(destination):
    """Build a self-contained, no-login PDF directly from the reviewed text."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    source = SOURCE.read_text(encoding="utf-8")
    if len(source) < 1500 or not source.startswith("# CIKGULAJU AI"):
        raise ValueError("Manual source unavailable or unexpected")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    navy = colors.HexColor("#143047")
    teal = colors.HexColor("#117E8A")
    grey = colors.HexColor("#435668")
    normal = ParagraphStyle(
        "ManualBody", fontName="Helvetica", fontSize=9.2,
        leading=13.4, textColor=navy, spaceAfter=6.0)
    heading = ParagraphStyle(
        "ManualHeading", parent=normal, fontName="Helvetica-Bold",
        fontSize=12.4, leading=17.0, spaceBefore=13,
        spaceAfter=8, textColor=teal, keepWithNext=True)
    title = ParagraphStyle(
        "ManualTitle", parent=normal, fontName="Helvetica-Bold",
        fontSize=23, leading=27, alignment=TA_CENTER,
        textColor=navy, spaceBefore=12, spaceAfter=12)
    subtitle = ParagraphStyle(
        "ManualSubtitle", parent=normal, fontName="Helvetica-Bold",
        fontSize=11, leading=15, alignment=TA_CENTER,
        textColor=grey, spaceAfter=15)
    bullet = ParagraphStyle(
        "ManualBullet", parent=normal, leftIndent=14,
        firstLineIndent=-10, spaceAfter=4)
    step = ParagraphStyle(
        "ManualStep", parent=normal, leftIndent=14, spaceAfter=4)

    def safe(value):
        return escape(str(value), quote=False).replace("—", "-").replace("–", "-")

    story = []
    for raw in source.splitlines():
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 3))
        elif line.startswith("# "):
            story.append(Paragraph(safe(line[2:]), title))
        elif line.startswith("## "):
            if "MANUAL PENGGUNA" in line:
                story.append(Paragraph(safe(line[3:]), subtitle))
            else:
                story.append(Paragraph(safe(line[3:]), heading))
        elif line.startswith("- "):
            story.append(Paragraph("&#8226; " + safe(line[2:]), bullet))
        elif len(line) > 3 and line[0].isdigit() and line[1:3] == ". ":
            story.append(Paragraph(safe(line), step))
        else:
            story.append(Paragraph(safe(line), normal))

    def page_decor(canvas, doc):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(navy)
        canvas.rect(0, h - 20 * mm, w, 20 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(17 * mm, h - 12 * mm, "CIKGULAJU AI | MANUAL PENGGUNA")
        canvas.setFillColor(grey)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(17 * mm, 13 * mm, "Edisi 4 November 2026 | Telegram CikguLaju")
        canvas.drawRightString(w - 17 * mm, 13 * mm, "Halaman %d" % doc.page)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(destination), pagesize=A4,
        leftMargin=17 * mm, rightMargin=17 * mm,
        topMargin=26 * mm, bottomMargin=20 * mm,
        title="Manual Pengguna CikguLaju AI",
        author="CikguLaju AI")
    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    if destination.stat().st_size < 4000:
        raise ValueError("Generated manual PDF is too small")
    with destination.open("rb") as f:
        if f.read(5) != b"%PDF-":
            raise ValueError("Generated manual is not a PDF")
    return destination


def install(runtime):
    """Append one global button; retain user-specific referral navigation."""
    if getattr(runtime, "CIKGULAJU_MANUAL_PENGGUNA_INSTALLED", False):
        return True
    if any(not callable(getattr(runtime, name, None))
           for name in ("menu", "callback", "send", "send_document")):
        return False
    if not getattr(runtime, "API", None):
        return False

    original_menu = runtime.menu
    original_callback = runtime.callback

    def menu(cid, show_persistent=False):
        response = original_menu(cid, show_persistent=show_persistent)
        try:
            result = response.json().get("result") or {}
            mid = result.get("message_id")
            kb = (result.get("reply_markup") or {}).get("inline_keyboard") or []
            if not isinstance(mid, int) or mid <= 0 or not kb:
                raise ValueError("No editable inline menu available")
            new_kb = [[dict(b) for b in row] for row in kb]
            existing = {b.get("callback_data") for row in new_kb for b in row}
            if BUTTON["callback_data"] not in existing:
                where = next((i + 1 for i, row in enumerate(new_kb)
                              if any(b.get("callback_data") == "account"
                                     for b in row)), len(new_kb))
                new_kb.insert(where, [dict(BUTTON)])
            # Referral wrapper may already have edited Telegram's markup, but
            # the initial sendMessage response still carries the old keyboard.
            # Reinstate the referral entry only for verified invited members.
            lookup = getattr(runtime, "_private_referral_member", None)
            if callable(lookup):
                try:
                    member = lookup(cid)
                except Exception:
                    member = None
                if (isinstance(member, dict) and member.get("enabled") is True
                        and _REFERRAL_BUTTON["callback_data"] not in existing):
                    where = next((i + 1 for i, row in enumerate(new_kb)
                                  if any(b.get("callback_data") == BUTTON["callback_data"]
                                         for b in row)), len(new_kb))
                    new_kb.insert(where, [dict(_REFERRAL_BUTTON)])
            if new_kb != kb:
                result = requests.post(
                    str(runtime.API) + "/editMessageReplyMarkup",
                    json={"chat_id": cid, "message_id": mid,
                          "reply_markup": {"inline_keyboard": new_kb}},
                    timeout=12)
                if not result.ok or (result.json() or {}).get("ok") is not True:
                    raise RuntimeError("Menu update not acknowledged")
        except Exception as exc:
            print("USER MANUAL menu fallback:", type(exc).__name__, flush=True)
            try:
                runtime.send(cid, "📖 <b>Manual Pengguna CikguLaju</b>",
                             [[dict(BUTTON)]])
            except Exception:
                pass
        return response

    def callback(cid, data):
        if str(data or "") != BUTTON["callback_data"]:
            return original_callback(cid, data)
        try:
            with TemporaryDirectory(prefix="cikgulaju_manual_") as tmp:
                pdf = build_pdf(Path(tmp) / "Manual_Pengguna_CikguLaju_AI_2026.pdf")
                result = runtime.send_document(
                    cid, str(pdf), "Manual Pengguna CikguLaju AI (PDF) - Percuma")
                check = getattr(runtime, "_telegram_delivery_ok_v25279", None)
                if callable(check):
                    ok = bool(check(result))
                else:
                    ok = (bool(getattr(result, "ok", False))
                          and (result.json() or {}).get("ok") is True)
                if not ok:
                    raise RuntimeError("Telegram has not acknowledged PDF")
                return result
        except Exception as exc:
            print("USER MANUAL PDF delivery failed:", type(exc).__name__, flush=True)
            return runtime.send(
                cid, "⚠️ Manual PDF belum dapat dihantar. Sila cuba lagi.",
                [[dict(BUTTON)], [{"text": "🏠 Menu Utama", "callback_data": "home"}]])

    runtime.menu = menu
    runtime.callback = callback
    runtime.CIKGULAJU_MANUAL_PENGGUNA_INSTALLED = True
    return True
