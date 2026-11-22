"""Fill the existing KP2027 Year 1 RPT cover for authorized paid teachers.

Source documents are SHA verified by kp2027_year1_rpt_combined and never modified.
Free/expired teachers always get the unchanged source file. No name or logo is
accepted from an HTTP query/body; it is resolved from their signed session.
"""
from copy import deepcopy
from io import BytesIO


def _clean(value, maximum):
    if not isinstance(value, str) or len(value) > maximum or any(ord(x) < 32 for x in value):
        raise ValueError("School identity field is not valid")
    return value.strip()


def _identity_fields(identity):
    if not isinstance(identity, dict):
        raise ValueError("School identity missing")
    school = _clean(identity.get("school") or "", 160)
    teacher = _clean(identity.get("teacher") or "", 100)
    state = _clean(identity.get("state") or "", 40)
    if teacher.casefold() == "cikgu":
        teacher = ""
    logo = identity.get("logo")
    if logo is not None and (not isinstance(logo, bytes) or not logo.startswith(b"\x89PNG\r\n\x1a\n") or len(logo) > 700_000):
        raise ValueError("School logo must be a validated PNG")
    return school, teacher, state, logo


def _word_logo(paragraph, png):
    """Add the school crest as a floating front-page drawing without reflow."""
    from docx.shared import Inches
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from copy import deepcopy

    run = paragraph.add_run()
    shape = run.add_picture(BytesIO(png), width=Inches(0.73))
    inline = shape._inline
    # Word's position relative to the physical A4 landscape page, not margins.
    anchor = OxmlElement("wp:anchor")
    for name, value in (("distT", "0"), ("distB", "0"), ("distL", "0"),
                        ("distR", "0"), ("simplePos", "0"), ("relativeHeight", "1"),
                        ("behindDoc", "0"), ("locked", "0"),
                        ("layoutInCell", "1"), ("allowOverlap", "1")):
        anchor.set(name, value)
    pos = OxmlElement("wp:simplePos")
    pos.set("x", "0")
    pos.set("y", "0")
    anchor.append(pos)
    for axis, pos_offset in (("H", 440_000), ("V", 490_000)):
        item = OxmlElement("wp:position" + axis)
        item.set("relativeFrom", "page")
        offset = OxmlElement("wp:posOffset")
        offset.text = str(pos_offset)
        item.append(offset)
        anchor.append(item)
    anchor.append(deepcopy(inline.extent))
    anchor.append(OxmlElement("wp:wrapNone"))
    for child in inline:
        if child.tag in {qn("wp:docPr"), qn("wp:cNvGraphicFramePr"), qn("a:graphic")}:
            anchor.append(deepcopy(child))
    inline.getparent().replace(inline, anchor)


def personalize_docx(original, identity):
    """Update only editable cover cells; keep all 788 PdP rows and source styles."""
    from docx import Document
    from docx.shared import Pt, RGBColor
    school, teacher, state, logo = _identity_fields(identity)
    if not (school or teacher or state or logo):
        return original
    doc = Document(BytesIO(original))
    if not doc.tables or len(doc.tables[0].rows) != 6:
        raise ValueError("Unexpected original RPT cover")
    cover = doc.tables[0]
    expected = {(0, 0): "NAMA SEKOLAH", (0, 2): "NEGERI",
                (2, 2): "NAMA GURU", (4, 0): "DISEDIAKAN OLEH"}
    for (r, c), label in expected.items():
        if cover.cell(r, c).text.strip() != label:
            raise ValueError("Unexpected RPT cover field")
    for row, col, value in ((0, 1, school), (0, 3, state),
                            (2, 3, teacher), (4, 1, teacher)):
        if not value:
            continue
        cell = cover.cell(row, col)
        p = cell.paragraphs[0]
        # Blank original cells contain no runs. Preserve original table styles.
        for run in list(p.runs):
            run.text = ""
        run = p.add_run(value)
        run.font.name = "Aptos"
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(32, 56, 79)
    if logo:
        _word_logo(doc.paragraphs[0], logo)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _fit_pdf_text(page, text, rect, *, maximum=8):
    """Fit a field within the existing cover row; never truncate identity."""
    import fitz
    if not text:
        return
    for size in (maximum, 7.5, 7, 6.5, 6, 5.5, 5):
        # The shape API lets us verify a fit before committing ink to the page.
        shape = page.new_shape()
        remaining = shape.insert_textbox(fitz.Rect(*rect), text, fontsize=size,
                                         fontname="helv", color=(0.125, 0.22, 0.31),
                                         align=fitz.TEXT_ALIGN_LEFT, lineheight=1.0)
        if remaining >= 0:
            shape.commit(overlay=True)
            return
    raise ValueError("Name does not fit RPT field")


def personalize_pdf(original, identity):
    """Stamp only the original A4 landscape first-page blanks, no new cover."""
    import fitz
    school, teacher, state, logo = _identity_fields(identity)
    if not (school or teacher or state or logo):
        return original
    source = fitz.open(stream=original, filetype="pdf")
    try:
        if not source.page_count or abs(source[0].rect.width - 841.89) > 2 or abs(source[0].rect.height - 595.3) > 2:
            raise ValueError("Unexpected RPT page dimensions")
        cover = source[0]
        for label in ("NAMA SEKOLAH", "NEGERI", "NAMA GURU", "DISEDIAKAN OLEH"):
            if len([area for area in cover.search_for(label) if area.y0 < 240]) != 1:
                raise ValueError("Expected RPT cover label missing")
        # These rectangles are the four blank value cells on the source PDF.
        _fit_pdf_text(cover, school, (139, 130, 414, 147.5))
        _fit_pdf_text(cover, state, (531, 130, 805, 147.5))
        _fit_pdf_text(cover, teacher, (531, 166.5, 805, 185))
        _fit_pdf_text(cover, teacher, (139, 203.5, 414, 221))
        if logo:
            cover.insert_image(fitz.Rect(35, 42, 108, 114), stream=logo, keep_proportion=True, overlay=True)
        result = source.tobytes(garbage=3, deflate=True)
        if not result.startswith(b"%PDF-") or len(result) > 10_000_000:
            raise ValueError("Stamped RPT is invalid")
        return result
    finally:
        source.close()


def for_download(account, subject, fmt, original):
    """Keep free output generic; paid identity comes solely from teacher profile."""
    from web.english_rpt_2027_http import _has_paid_access
    if not _has_paid_access(account):
        return original, False
    from web.teacher_profile_store import ProfileUnavailable
    from web.rpt_school_cover import school_identity
    from web_v1_telegram_auth_routes import _config
    uid = account.get("telegram_user_id") if isinstance(account, dict) else None
    if type(uid) is not int or uid < 1:
        raise ProfileUnavailable("Akaun guru tidak sah")
    config = _config()
    if not config or config.get("account_backend") != "supabase":
        raise ProfileUnavailable("Profil sekolah tidak dapat disemak")
    identity = school_identity(config, uid, allow_teacher_only=True)
    if identity is None:
        return original, False
    try:
        final = personalize_pdf(original, identity) if fmt == "pdf" else personalize_docx(original, identity)
    except (ValueError, RuntimeError, TypeError, OSError) as ex:
        raise ProfileUnavailable("RPT dengan identiti sekolah tidak dapat disediakan") from None
    return final, final != original
