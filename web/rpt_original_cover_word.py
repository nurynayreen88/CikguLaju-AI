"""Build editable RPT cover and continuous tables from verified sources, private QA.

Preserve existing PDF cover artwork exactly (not a redesigned cover). In Word
the original cover artwork is embedded; the body is a fully editable table.
Only the three approved identity areas may be filled, using saved paid profile.
"""
from io import BytesIO
from hashlib import sha256
from pathlib import Path
import json
import fitz
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def cover_layout(root, subject, year, source):
    ledger=json.loads((Path(root)/"web_2027_pdfs/original_cover_layout_verified.json").read_text("utf8"))
    key=f"{subject}:{year}"
    digest=sha256(Path(source).read_bytes()).hexdigest()
    candidates=[ledger.get("aligned_rpt_covers",{}).get(key,{}),
                ledger.get("science_year6_covers",{}).get(key,{}),
                ledger.get("english_integrated",{}),ledger]
    for layout in candidates:
        if layout.get("source_sha256_by_subject_year",{}).get(key)==digest:
            return layout
    raise ValueError("Cover source not locked to the approved template")

def cover_page(source,layout,identity=None):
    original=fitz.open(source)
    out=fitz.open()
    try:
        out.insert_pdf(original,from_page=0,to_page=0)
        page=out[0]
        if (abs(page.rect.width-layout["page_width"])>layout["tolerance_pt"]
            or abs(page.rect.height-layout["page_height"])>layout["tolerance_pt"]):
            raise ValueError("Original cover geometry mismatch")
        if identity is not None:
            from web.kp2027_year1_rpt_personalize import _identity_fields
            school,teacher,_,logo=_identity_fields(identity)
            from web.kp2027_year1_rpt_personalize import _fit_pdf_text
            if logo:
                page.draw_rect(fitz.Rect(layout["logo_interior_top_left"]),
                               color=None,fill=tuple(layout.get("logo_background_rgb",[1,1,1])),overlay=True)
                page.insert_image(fitz.Rect(layout["logo_image_safe_top_left"]),
                                  stream=logo,keep_proportion=True,overlay=True)
            for field,value in (("school_row_top_left",school),("teacher_row_top_left",teacher)):
                if value:
                    rect=fitz.Rect(layout[field])
                    page.draw_rect(rect,color=None,fill=tuple(layout["identity_background_rgb"]),overlay=True)
                    _fit_pdf_text(page,value,rect+ (3,2,-3,-2),maximum=10)
        return out.tobytes(garbage=4,deflate=True)
    finally:
        original.close()
        out.close()

def attach_original_cover(doc,pdf_cover):
    """Place only the cover as original artwork; never rasterize teaching tables."""
    with fitz.open(stream=pdf_cover,filetype="pdf") as pdf:
        if len(pdf)!=1: raise ValueError("Expected exactly one cover")
        png=pdf[0].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).tobytes("png")
    sec=doc.sections[0]
    sec.page_width=Cm(29.7);sec.page_height=Cm(21)
    sec.left_margin=sec.right_margin=sec.top_margin=sec.bottom_margin=Cm(.3)
    sec.header_distance=sec.footer_distance=Cm(0)
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
    p.paragraph_format.line_spacing=1
    run=p.add_run()
    shape=run.add_picture(BytesIO(png),width=Cm(28.65))
    shape._inline.docPr.set("descr","CIKGULAJU_ORIGINAL_RPT_COVER")
    body=doc.add_section(WD_SECTION_START.NEW_PAGE)
    body.left_margin=body.right_margin=Cm(1.15)
    body.top_margin=body.bottom_margin=Cm(1.05)
    body.header_distance=body.footer_distance=Cm(.45)
    body.header.is_linked_to_previous=False
    body.footer.is_linked_to_previous=False
    return body

def replace_cover_image(original,source,layout,identity):
    """Paid download integration primitive: body XML and all rows unchanged."""
    from docx import Document
    doc=Document(BytesIO(original))
    shapes=[s for s in doc.inline_shapes
            if s._inline.docPr.get("descr")=="CIKGULAJU_ORIGINAL_RPT_COVER"]
    if len(shapes)!=1: raise ValueError("No unique original cover")
    shape=shapes[0]
    rel=shape._inline.xpath(".//a:blip")[0].get(qn("r:embed"))
    part=doc.part.related_parts[rel]
    with fitz.open(stream=cover_page(source,layout,identity),filetype="pdf") as pdf:
        part._blob=pdf[0].get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).tobytes("png")
    result=BytesIO();doc.save(result)
    return result.getvalue()


def for_paid_download(account,original,source,layout):
    """Reuse the signed-session profile; never accept browser identity values."""
    from web.english_rpt_2027_http import _has_paid_access
    from web.teacher_profile_store import ProfileUnavailable
    if not _has_paid_access(account):
        raise PermissionError("RPT Word hanya untuk pengguna berbayar aktif")
    uid=account.get("telegram_user_id")
    if type(uid) is not int or uid<1:
        raise ProfileUnavailable("Akaun guru tidak sah")
    from web_v1_telegram_auth_routes import _config
    from web.rpt_school_cover import school_identity
    config=_config()
    if not config or config.get("account_backend")!="supabase":
        raise ProfileUnavailable("Profil sekolah tidak dapat disemak")
    identity=school_identity(config,uid,allow_teacher_only=True)
    if identity is None:
        return original,False
    try:
        updated=replace_cover_image(original,source,layout,identity)
    except (ValueError,RuntimeError,TypeError,OSError):
        raise ProfileUnavailable("Muka depan RPT Word tidak dapat disediakan") from None
    return updated,updated!=original
