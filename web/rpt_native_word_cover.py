"""Source-locked RPT cover shared by private Word generation and profile QA.

Only the existing first-page graphic is rasterized for Word. Body tables
stay native/editable. PDF retains the source cover as a vector page.
Never accept identity data from query strings or expose premium files.
"""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import math

from web.kp2027_year1_rpt_personalize import _identity_fields
import fitz

def selected_layout(lock,key,digest):
    candidates=[lock,lock.get("full_standards_dlp_pdf_covers",{}),lock.get("english_integrated",{}),
                lock.get("aligned_rpt_covers",{}).get(key,{}),
                lock.get("science_year6_covers",{}).get(key,{}),
                lock.get("dlp_year"+key.rsplit(":",1)[-1],{}) if "_dlp:" in key else {}]
    for candidate in candidates:
        if candidate.get("source_sha256_by_subject_year",{}).get(key)==digest:
            return candidate
    raise ValueError("RPT original cover hash has no verified layout")

def _rect(layout,field,page):
    r=fitz.Rect(layout[field])
    if r.is_empty or not page.rect.contains(r):
        raise ValueError("Invalid original cover field")
    return r

def _color(layout,key,default=None):
    rgb=layout.get(key,default)
    if not isinstance(rgb,(list,tuple)) or len(rgb)!=3 or any(
            not isinstance(x,(int,float)) or not 0<=x<=1 for x in rgb):
        raise ValueError("Invalid original cover color")
    return rgb

def _text(page,area,value,fill):
    # Test fit before painting. No truncation and no extra identity page.
    for size in (12,11,10,9,8,7,6):
        shape=page.new_shape()
        available=shape.insert_textbox(area,value,fontsize=size,fontname="helv",
                                        color=(0.12,0.21,0.28),lineheight=1.05)
        if available>=0:
            page.draw_rect(area,color=None,fill=fill,overlay=True)
            shape.commit(overlay=True)
            return
    raise ValueError("Profile name does not fit the approved cover field")

def cover_png(pdf_bytes,lock,key,identity=None):
    digest=sha256(pdf_bytes).hexdigest()
    layout=selected_layout(lock,key,digest)
    with fitz.open(stream=pdf_bytes,filetype="pdf") as src,fitz.open() as cover:
        if len(src)<2: raise ValueError("RPT source has no body")
        cover.insert_pdf(src,from_page=0,to_page=0)
        page=cover[0]
        if abs(page.rect.width-layout["page_width"])>layout["tolerance_pt"] or abs(page.rect.height-layout["page_height"])>layout["tolerance_pt"]:
            raise ValueError("Original RPT cover dimensions changed")
        if identity:
            school,teacher,_,logo=_identity_fields(identity)
            if logo:
                interior=_rect(layout,"logo_interior_top_left",page)
                safe=_rect(layout,"logo_image_safe_top_left",page)
                if not interior.contains(safe): raise ValueError("Logo safe area not inside frame")
                page.draw_rect(interior,color=None,fill=_color(layout,"logo_background_rgb",(1,1,1)),overlay=True)
                page.insert_image(safe,stream=logo,keep_proportion=True,overlay=True)
            for value,field in ((school,"school_row_top_left"),(teacher,"teacher_row_top_left")):
                if value: _text(page,_rect(layout,field,page),value,_color(layout,"identity_background_rgb"))
        return page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).tobytes("png")

def add_word_cover(doc,png):
    """Place one full-page, source-derived cover image; suppress cover header/footer."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt
    sec=doc.sections[0]
    sec.different_first_page_header_footer=True
    sec.first_page_header.paragraphs[0].text=""
    sec.first_page_footer.paragraphs[0].text=""
    p=doc.add_paragraph()
    p.paragraph_format.space_after=Pt(0)
    p.paragraph_format.space_before=Pt(0)
    p.paragraph_format.line_spacing=Pt(1)
    shape=p.add_run().add_picture(BytesIO(png),width=sec.page_width,height=sec.page_height)
    inline=shape._inline
    anchor=OxmlElement("wp:anchor")
    for k,v in {"distT":"0","distB":"0","distL":"0","distR":"0",
                "simplePos":"0","relativeHeight":"0","behindDoc":"1","locked":"0",
                "layoutInCell":"1","allowOverlap":"1"}.items(): anchor.set(k,v)
    pos=OxmlElement("wp:simplePos");pos.set("x","0");pos.set("y","0");anchor.append(pos)
    for axis in ("H","V"):
        item=OxmlElement("wp:position"+axis);item.set("relativeFrom","page")
        offset=OxmlElement("wp:posOffset");offset.text="0";item.append(offset);anchor.append(item)
    anchor.append(deepcopy(inline.extent))
    anchor.append(OxmlElement("wp:wrapNone"))
    for child in inline:
        if child.tag in {qn("wp:docPr"),qn("wp:cNvGraphicFramePr"),qn("a:graphic")}:
            anchor.append(deepcopy(child))
    inline.getparent().replace(inline,anchor)
    doc.add_page_break()

def personalized_word(original,pdf_bytes,lock,key,account,config):
    """For future paid route: replace only the source cover image, not any table."""
    from web.english_rpt_2027_http import _has_paid_access
    from web.rpt_school_cover import school_identity
    from docx import Document
    from docx.oxml.ns import qn
    if not _has_paid_access(account): raise PermissionError("Paid RPT Word only")
    identity=school_identity(config,account.get("telegram_user_id"),allow_teacher_only=True)
    if not identity:return original
    doc=Document(BytesIO(original))
    anchors=doc.paragraphs[0]._p.xpath(".//wp:anchor")
    if len(anchors)!=1: raise ValueError("Source cover anchor missing")
    blips=anchors[0].xpath(".//a:blip")
    if len(blips)!=1: raise ValueError("Source cover picture missing")
    rid=blips[0].get(qn("r:embed"))
    part=doc.part.related_parts[rid]
    baseline=cover_png(pdf_bytes,lock,key)
    if sha256(part.blob).digest()!=sha256(baseline).digest():
        raise ValueError("Word cover does not match verified PDF source")
    replacement=cover_png(pdf_bytes,lock,key,identity)
    # Image part only. Body XML and all other source parts are untouched.
    part._blob=replacement
    out=BytesIO();doc.save(out)
    return out.getvalue()
