"""Personalize the new native RPT Word cover from the signed teacher account.
Call only after validating an approved private Word source; no legacy source guessing.
"""
from io import BytesIO

def personalize_word(original,identity):
    # Only the marked cover tables are changed, never the teaching grid.
    from web.kp2027_year1_rpt_personalize import _identity_fields
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt
    school,teacher,_,logo=_identity_fields(identity)
    if not any((school,teacher,logo)):return original
    doc=Document(BytesIO(original))
    if len(doc.tables)!=3 or doc.tables[0].cell(0,0).text!="LOGO SEKOLAH" or [doc.tables[1].cell(i,0).text for i in range(2)]!=["NAMA SEKOLAH","NAMA GURU"]:
        raise ValueError("Unrecognized Word cover")
    baseline=doc.tables[2]._tbl.xml
    if logo:
        cell=doc.tables[0].cell(0,0);cell.text=""
        p=cell.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        from PIL import Image
        with Image.open(BytesIO(logo)) as img:
            w,h=img.size
        scale=min(112/w,112/h)
        p.add_run().add_picture(BytesIO(logo),width=Pt(w*scale),height=Pt(h*scale))
    for i,value in enumerate((school,teacher)):
        if value:
            cell=doc.tables[1].cell(i,1)
            p=cell.paragraphs[0]
            if len(p.runs)!=1: raise ValueError("Unexpected RPT cover name cell")
            p.runs[0].text=value
            from docx.shared import Pt
            p.runs[0].font.size=Pt(10 if len(value)<90 else 8.5)
    assert doc.tables[2]._tbl.xml==baseline
    buf=BytesIO();doc.save(buf);return buf.getvalue()

def for_download(account, original):
    from web.english_rpt_2027_http import _has_paid_access
    from web.teacher_profile_store import ProfileUnavailable
    from web.rpt_school_cover import school_identity
    from web_v1_telegram_auth_routes import _config
    if not _has_paid_access(account):
        raise PermissionError("RPT Word hanya untuk pengguna berbayar aktif.")
    uid=account.get("telegram_user_id")
    config=_config()
    if type(uid) is not int or uid<1 or not config or config.get("account_backend")!="supabase":
        raise ProfileUnavailable("Profil sekolah tidak dapat disemak")
    identity=school_identity(config,uid,allow_teacher_only=True)
    if identity is None:return original,False
    try:
        data=personalize_word(original,identity)
    except (ValueError,RuntimeError,TypeError,OSError) as exc:
        raise ProfileUnavailable("Muka depan RPT Word tidak sepadan.") from None
    return data,data!=original
