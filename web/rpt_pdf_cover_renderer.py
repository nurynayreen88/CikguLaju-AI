"""Standalone RPT cover renderer. Runs on Telegram's existing PDF runtime.

Only adds a per-user school identity sheet and leaves all source pages intact.
No session, quota or database access.
"""
from io import BytesIO
from pathlib import Path

class ProfileUnavailable(Exception):
    pass


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
