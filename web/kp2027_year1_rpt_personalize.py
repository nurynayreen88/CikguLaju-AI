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
    """Fill exact historical RPT cover paragraphs; leave weekly tables untouched."""
    from docx import Document
    from docx.shared import Pt
    school, teacher, state, logo = _identity_fields(identity)
    if not (school or teacher or state or logo):
        return original
    doc = Document(BytesIO(original))
    if len(doc.paragraphs)<14 or not doc.tables or len(doc.tables[0].columns)!=5:
        raise ValueError("Unexpected classic RPT cover")
    markers={4:"NAMA SEKOLAH:", 5:"SUBJEK:", 7:"KUMPULAN:", 8:"NAMA GURU:",10:"Disediakan oleh:"}
    for i, label in markers.items():
        if not doc.paragraphs[i].text.startswith(label):
            raise ValueError("Expected original RPT cover label missing")
    def update(i, value, preferred=11):
        if not value: return
        p=doc.paragraphs[i]
        if len(p.runs)!=1: raise ValueError("Classic cover run structure changed")
        p.runs[0].text=value
        # Shrink only unusually long values, preserving original typography otherwise.
        if len(value)>95: p.runs[0].font.size=Pt(8.5)
        elif len(value)>75: p.runs[0].font.size=Pt(10)
    update(4, "NAMA SEKOLAH: "+school)
    update(8, "NAMA GURU: "+teacher)
    if state:
        p=doc.paragraphs[7]
        if len(p.runs)!=1 or "NEGERI:" not in p.text: raise ValueError("Original state field missing")
        p.runs[0].text=p.text.split("NEGERI:",1)[0]+"NEGERI: "+state
    if teacher:
        update(10,"Disediakan oleh: "+teacher+"     Disemak oleh: ____________________")
    if logo:
        _word_logo(doc.paragraphs[0],logo)
    buf=BytesIO();doc.save(buf)
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
    """Populate historical free-form 2027 cover, preserving source page count."""
    import fitz
    school, teacher, state, logo = _identity_fields(identity)
    if not (school or teacher or state or logo):
        return original
    document=fitz.open(stream=original,filetype="pdf")
    try:
        if not document.page_count or abs(document[0].rect.width-841.89)>2 or abs(document[0].rect.height-595.3)>2:
            raise ValueError("Unexpected RPT page dimensions")
        page=document[0]
        for label in ("RANCANGAN PENGAJARAN TAHUNAN","NAMA SEKOLAH:","NAMA GURU:","Disediakan oleh:"):
            if len(page.search_for(label))!=1:
                raise ValueError("Original RPT cover field not found")
        # Coordinates are locked to the verified original A4 landscape cover.
        # Redact only underscore placeholders, never text labels or any PdP table.
        fields=[
          (school,(338,257,620,285),(344,255,620,283)),
          (teacher,(312,381,617,408),(317,379,617,407)),
          (state,(485,349,610,377),(490,348,615,376)),
          (teacher,(329,453,426,477),(331,453,424,476)),
        ]
        # The original 'Disemak oleh:' label begins at x=433; never redact it.
        for value,erase,area in fields:
            if value:page.add_redact_annot(fitz.Rect(*erase),fill=(1,1,1),cross_out=False)
        if any(v for v,_,_ in fields): page.apply_redactions(images=0,graphics=0,text=0)
        for i,(value,erase,area) in enumerate(fields):
            if not value:continue
            # Very long teacher names still appear in the generous NAMA GURU
            # field, but need not force the much shorter 'Disediakan' slot.
            if i==3:
                try: _fit_pdf_text(page,value,area,maximum=8)
                except ValueError: pass
            else:_fit_pdf_text(page,value,area,maximum=10)
        if logo:
            page.insert_image(fitz.Rect(36,43,107,111),stream=logo,keep_proportion=True,overlay=True)
        data=document.tobytes(garbage=3,deflate=True)
        if not data.startswith(b"%PDF-") or len(data)>10_000_000:
            raise ValueError("Invalid personalized RPT PDF")
        return data
    finally:
        document.close()


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
