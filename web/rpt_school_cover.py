"""Add a per-teacher school identity sheet to downloaded RPT PDFs.

The original RPT PDF is never edited, deleted, or replaced. The added first
page carries a school name and logo from authenticated private profile data.
Return original bytes when the teacher has not saved school identity.
"""
from io import BytesIO
from pathlib import Path

from web.teacher_profile_store import _get_one, ProfileUnavailable, _validated_name
from web.school_logo_store import logo_png


def school_identity(config, uid):
    """Teacher identity comes from the signed Web session, not browser params."""
    if type(uid) is not int or uid < 1:
        raise ProfileUnavailable("Akaun guru tidak sah")
    row = _get_one(
        config["supabase_url"], config["supabase_key"],
        "teacher_profiles", uid,
        "telegram_user_id,display_name,school_name,state_name")
    row = row or {}
    school = _validated_name(row.get("school_name") or "", 160, "Nama sekolah")
    teacher = _validated_name(row.get("display_name") or "", 100, "Nama guru")
    state = _validated_name(row.get("state_name") or "", 40, "Negeri sekolah")
    logo = logo_png(config["supabase_url"], config["supabase_key"], uid)
    if not school and logo is None:
        return None
    return {"school": school, "teacher": teacher, "state": state, "logo": logo}


def for_download(account, path, subject, year):
    """Return original PDF file path OR personalized in-memory PDF.

    No personalization for anonymous/legacy test accounts without a Telegram
    identity. Real Web accounts are already authenticated before this call.
    """
    uid = account.get("telegram_user_id") if isinstance(account, dict) else None
    if type(uid) is not int or uid <= 0:
        return path
    from web_v1_telegram_auth_routes import _config
    config = _config()
    if not config or config.get("account_backend") != "supabase":
        raise ProfileUnavailable("Profil sekolah tidak dapat disemak")
    identity = school_identity(config, uid)
    if identity is None:
        return path
    return personalized_pdf(path, subject, year, identity)


def _fit_line(text, font, size, width):
    """Fit one line without drawing outside the printable content area."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = str(text or "").split()
    result = []
    for word in words:
        candidate = (" ".join(result + [word]))
        if stringWidth(candidate, font, size) <= width:
            result.append(word)
        else:
            if result:
                break
            # An unbroken long school name still cannot escape the page.
            chars = ""
            for char in word:
                if stringWidth(chars + char, font, size) > width:
                    break
                chars += char
            return chars
    return " ".join(result)


def personalized_pdf(source_path, subject, year, identity):
    """Prepend a clear landscape-compatible identity page; retain every source page."""
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase.pdfmetrics import stringWidth

    path = Path(source_path)
    if path.is_symlink() or not path.is_file():
        raise ProfileUnavailable("RPT asal belum tersedia")
    try:
        raw = path.read_bytes()
        if not raw.startswith(b"%PDF-"):
            raise ValueError("Not PDF")
        original = PdfReader(BytesIO(raw), strict=True)
        if not original.pages or len(original.pages) > 300:
            raise ValueError("Unexpected source pages")
        width = float(original.pages[0].mediabox.width)
        height = float(original.pages[0].mediabox.height)
        if not 400 <= width <= 1200 or not 400 <= height <= 1200:
            raise ValueError("Unexpected paper size")

        margin = max(30, min(width, height) * 0.07)
        background = HexColor("#F6FAFC")
        blue = HexColor("#143B5B")
        teal = HexColor("#08796C")
        muted = HexColor("#5C7384")
        line = HexColor("#DCE8EE")
        overlay = BytesIO()
        c = canvas.Canvas(overlay, pagesize=(width, height), pageCompression=1)
        c.setFillColor(background)
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setFillColor(blue)
        c.rect(0, height - 64, width, 64, fill=1, stroke=0)
        c.setFillColor(HexColor("#54D1BD"))
        c.rect(0, height - 68, width, 4, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor("#FFFFFF"))
        c.drawString(margin, height - 39, "RANCANGAN PENGAJARAN TAHUNAN")
        c.setFillColor(teal)
        c.setFont("Helvetica-Bold", 26)
        c.drawCentredString(width / 2, height - 113, str(year))
        c.setFillColor(muted)
        c.setFont("Helvetica", 10)
        c.drawCentredString(width / 2, height - 133, "LEMBARAN MAKLUMAT SEKOLAH")
        image = identity.get("logo")
        if image:
            logo_size = min(113, max(80, height * 0.19))
            c.drawImage(ImageReader(BytesIO(image)), (width - logo_size) / 2,
                        height * 0.55, width=logo_size, height=logo_size,
                        preserveAspectRatio=True, anchor="c", mask="auto")
        school = identity.get("school") or ""
        title_y = height * (0.48 if image else 0.64)
        c.setFillColor(blue)
        c.setFont("Helvetica-Bold", 19)
        if school:
            max_width = width - 2 * margin - 30
            first = _fit_line(school, "Helvetica-Bold", 19, max_width)
            c.drawCentredString(width / 2, title_y, first)
            remain = school[len(first):].strip()
            if remain:
                c.setFont("Helvetica-Bold", 17)
                second = _fit_line(remain, "Helvetica-Bold", 17, max_width)
                c.drawCentredString(width / 2, title_y - 25, second)
        else:
            c.drawCentredString(width / 2, title_y, "LOGO SEKOLAH")
        state = identity.get("state") or ""
        if state:
            c.setFillColor(muted)
            c.setFont("Helvetica", 11)
            c.drawCentredString(width / 2, title_y - 52, state)
        c.setStrokeColor(line)
        c.setLineWidth(1)
        c.line(margin, height * 0.31, width - margin, height * 0.31)
        c.setFillColor(blue)
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(width / 2, height * 0.245,
                            _fit_line(subject, "Helvetica-Bold", 15, width - 2 * margin))
        teacher = identity.get("teacher") or ""
        if teacher and teacher.casefold() != "cikgu":
            c.setFillColor(muted)
            c.setFont("Helvetica", 10)
            c.drawCentredString(width / 2, height * 0.19,
                                _fit_line("Disediakan oleh: " + teacher,
                                          "Helvetica", 10, width - 2 * margin))
        c.setFillColor(muted)
        c.setFont("Helvetica", 8)
        c.drawCentredString(width / 2, 27,
                            "Lembaran profil sekolah • RPT asal dikekalkan tanpa perubahan")
        c.save()
        overlay.seek(0)

        front = PdfReader(overlay)
        writer = PdfWriter()
        writer.add_page(front.pages[0])
        for page in original.pages:
            writer.add_page(page)
        final = BytesIO()
        writer.write(final)
        final.seek(0)
        return final
    except Exception:
        raise ProfileUnavailable("RPT sekolah tidak dapat disediakan. RPT asal tidak diubah.") from None
