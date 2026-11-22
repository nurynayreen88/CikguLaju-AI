"""Common reflection policy for verified CikguLaju RPH (KSSR / KP2027).

A reflection must never fabricate a count or claim mastery. Adapt wording and
follow-up to a verified success criterion or learning objective. Unverified
document layouts are left unchanged, including the historical PI v2 archive.
"""
from __future__ import annotations
from io import BytesIO
import re

from web.kp2027_pilot_teacher_fields import _proposed_support_action, _clean_success_criterion

CRITERIA = {"kriteria kejayaan", "success criteria", "success criterion"}
OBJECTIVES = {"objektif pembelajaran", "learning objectives", "learning objective"}
REFLECTION = {"refleksi", "reflection", "refleksi auto manual", "refleksi auto / manual"}

def _key(value):
    return " ".join(re.sub(r"[^\w ]+", " ", str(value).casefold()).split())


def _clean(value):
    return _clean_success_criterion(value)


def _english_action(criterion):
    v=criterion.casefold()
    if any(x in v for x in ("read", "reading", "comprehension", "text")):
        return "guided reading and comprehension practice using a short text"
    if any(x in v for x in ("write", "writing", "sentence", "spell")):
        return "guided sentence writing and spelling correction"
    if any(x in v for x in ("listen", "listening", "audio")):
        return "targeted listening and repeated audio practice"
    if any(x in v for x in ("speak", "speaking", "pronounc", "oral")):
        return "guided oral practice with modelling and partner feedback"
    if any(x in v for x in ("vocabulary", "words", "word")):
        return "picture-and-word matching and vocabulary recall practice"
    return "targeted small-group practice followed by a reassessment"


def candidates(criterion, subject=""):
    criterion=_clean(criterion)
    if subject in ("ENGLISH", "MATH_DLP", "SCIENCE_DLP"):
        clause=criterion.strip(" .")
        action=_english_action(clause)
        return (
            "The lesson was conducted as planned. ____ pupils met the success criterion: "
            + clause + ". ____ pupils have not yet met it and will complete " + action + ".",
            "____ pupils met the criterion: " + clause + ". "
            "____ pupils have not yet met it; follow-up: " + action + ".",
        )
    action,short=_proposed_support_action(criterion)
    phrase=criterion[6:] if criterion.casefold().startswith("murid ") else criterion
    phrase=phrase[0].lower()+phrase[1:]
    return (
        "PdP dilaksanakan mengikut perancangan. ____ orang murid menguasai kemahiran "
        + phrase + ". ____ orang murid belum menguasai dan akan mengikuti " + action + ".",
        "____ orang murid menguasai kemahiran " + phrase +
        ". ____ orang murid belum menguasai; tindakan: " + short + ".",
    )


def criterion_from_layout(layout):
    """Return only real metadata; do not invent a SK/SP or success criterion."""
    if not isinstance(layout,dict):
        return ""
    header=layout.get("header")
    if not isinstance(header,list):
        return ""
    for keys in (CRITERIA, OBJECTIVES):
        for entry in header:
            if isinstance(entry,dict) and _key(entry.get("label")) in keys:
                value=str(entry.get("value") or "").strip()
                if 12<=len(value)<=380 and value!="—":
                    return _clean(value)
    return ""


def personalize_layout(layout, teacher, subject):
    """Mutate only reflection footer of a verified Telegram-style layout."""
    if not isinstance(layout,dict) or layout.get("style")!="telegram-native-rph-v1":
        return False
    footer=layout.get("footer")
    if not isinstance(footer,list):
        return False
    rows=[row for row in footer if isinstance(row,dict) and _key(row.get("label")) in REFLECTION]
    if len(rows)!=1:
        return False
    # Auto/Manual selects the Web input mode; it is never a printed label.
    if _key(rows[0].get("label")) == "refleksi auto manual":
        rows[0]["label"] = "Refleksi"
    if teacher.get("reflection"):
        rows[0]["value"]=teacher["reflection"]
        return True
    criterion=criterion_from_layout(layout)
    if not criterion:
        return False
    rows[0]["value"]=candidates(criterion,subject)[0]
    return True


def _docx_rewrite(original, subject):
    from docx import Document
    from docx.enum.table import WD_ROW_HEIGHT_RULE

    source = Document(BytesIO(original))
    named = []
    reflection_rows = []
    for table in source.tables:
        for row in table.rows:
            if len(row.cells) >= 2:
                name = _key(row.cells[0].text)
                named.append((name, row.cells[1]))
                if name in REFLECTION:
                    reflection_rows.append(row)
    if len(reflection_rows) != 1:
        return original
    criterion = ""
    for labels in (CRITERIA, OBJECTIVES):
        opts = [cell.text for name, cell in named if name in labels]
        if len(opts) == 1 and 12 <= len(opts[0].strip()) <= 380:
            criterion = _clean(opts[0])
            break
    if not criterion:
        return original

    row = reflection_rows[0]
    label_cell, value_cell = row.cells[0], row.cells[1]
    # Preserve the label's original font/bold/colour and its shaded cell.
    if _key(label_cell.text) == "refleksi auto manual":
        label_runs = [run for p in label_cell.paragraphs for run in p.runs]
        if not label_runs:
            return original
        label_runs[0].text = "Refleksi"
        for run in label_runs[1:]:
            run.text = ""

    # Editing the original run (instead of cell.text) preserves font, size,
    # paragraph spacing, alignment and runs in this verified table template.
    paragraphs = value_cell.paragraphs
    if not paragraphs:
        return original
    text = candidates(criterion, subject)[0]
    first = paragraphs[0]
    if first.runs:
        first.runs[0].text = text
        for run in first.runs[1:]:
            run.text = ""
    else:
        first.add_run(text)
    for paragraph in paragraphs[1:]:
        # Extra paragraphs used only for old reflection wording may be safely
        # dropped; never remove drawings or images from an unknown template.
        if paragraph._element.xpath('.//w:drawing|.//w:object|.//w:pict'):
            return original
        paragraph._element.getparent().remove(paragraph._element)

    # A historical fixed-height blank reflection area must not force a large
    # empty box or clip a longer manual note in a Word copy.
    if row.height is not None and row.height.pt >= 72:
        row.height = None
        row.height_rule = WD_ROW_HEIGHT_RULE.AUTO
    out = BytesIO()
    source.save(out)
    return out.getvalue()


def _pdf_rewrite(original, subject):
    """Only touch a one-page, ruled two-column table with verifiable cell edges."""
    import fitz
    document=fitz.open(stream=original,filetype="pdf")
    try:
        if len(document)!=1:
            return original
        page=document[0]
        W,H=page.rect.width,page.rect.height
        drawings=page.get_drawings()
        vertical=[p["rect"] for p in drawings if p.get("type")=="s" and
                  p["rect"].height>15 and p["rect"].width<1.5]
        horizontals=[p["rect"] for p in drawings if p.get("type")=="s" and
                     p["rect"].width>W*0.55 and p["rect"].height<1.5]
        if not vertical or len(horizontals)<4:
            return original

        def row(name):
            labels=[r for r in page.search_for(name) if r.x0 < W*0.35]
            if len(labels)!=1:
                return None
            anchor=labels[0]
            separator=[v for v in vertical if anchor.x1+5<v.x0<W*0.48
                       and v.y0<=anchor.y0 and v.y1>=anchor.y1]
            rights=[v for v in vertical if v.x0>W*0.75 and
                    v.y0<=anchor.y0 and v.y1>=anchor.y1]
            above=[h for h in horizontals if h.y0<=anchor.y0 and anchor.y0-h.y0<65]
            below=[h for h in horizontals if h.y0>=anchor.y1 and h.y0-anchor.y1<130]
            if len(separator)!=1 or len(rights)!=1 or not above or not below:
                return None
            top=max(h.y0 for h in above); bottom=min(h.y0 for h in below)
            box=fitz.Rect(separator[0].x0+4,top+3,rights[0].x0-4,bottom-3)
            if not (box.width>150 and box.height>20):
                return None
            return box
        reflection=row("Refleksi") or row("Reflection")
        if reflection is None:
            return original
        criterion_box=None
        for label in ("Kriteria Kejayaan","Success Criteria","Objektif Pembelajaran","Learning Objectives"):
            criterion_box=row(label)
            if criterion_box is not None:
                break
        if criterion_box is None:
            return original
        criterion=" ".join(page.get_text("text",clip=criterion_box,sort=True).split())
        if not 12<=len(criterion)<=380:
            return original
        # PDFs with complex-script/RTL glyphs are preserved until their
        # font/layout-specific renderer is separately certified.
        if any("\u0600"<=ch<="\u08ff" for ch in criterion):
            return original
        chosen=None
        for sentence in candidates(criterion,subject):
            sentence=sentence.replace("–","-").replace("—","-")
            try:sentence.encode("latin-1")
            except UnicodeEncodeError:continue
            for size in (8.3,7.5,7,6.4):
                temp=fitz.open();dummy=temp.new_page(width=W,height=H)
                remaining=dummy.insert_textbox(reflection,sentence,fontname="helv",fontsize=size,lineheight=1.03)
                temp.close()
                if remaining>=0:
                    chosen=(sentence,size)
                    break
            if chosen:
                break
        if chosen is None:
            return original
        page.add_redact_annot(reflection,fill=(1,1,1),cross_out=False)
        page.apply_redactions(images=0,graphics=0,text=0)
        if page.insert_textbox(reflection,chosen[0],fontname="helv",
                               fontsize=chosen[1],lineheight=1.03)<0:
            return original
        result=document.tobytes(garbage=4,deflate=True)
        return result if result.startswith(b"%PDF-") else original
    finally:
        document.close()


def personalize_verified_document(document,fmt,selection):
    """Best-effort safe copy. Unknown templates always return original bytes.

    PI v2 private source is explicitly excluded. Manual teacher reflections
    always take precedence over automatic generation.
    """
    if not isinstance(document,BytesIO) or not isinstance(selection,dict):
        return document
    if selection.get("source")=="pi-696-private-bundle" or (
        selection.get("teacher") or {}).get("reflection"):
        return document
    subject=selection.get("subject")
    if not isinstance(subject,str):
        return document
    source=document.getvalue()
    try:
        if fmt=="word" and source.startswith(b"PK\x03\x04"):
            result=_docx_rewrite(source,subject)
        elif fmt=="pdf" and source.startswith(b"%PDF-"):
            result=_pdf_rewrite(source,subject)
        else:
            return document
        if result==source or len(result)>15*1024*1024:
            return document
        return BytesIO(result)
    except Exception:
        # Preserve an otherwise verified source RPH rather than break downloads.
        return document
