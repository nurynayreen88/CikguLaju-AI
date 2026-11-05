"""Telegram-style A4 RPH Word writer with 3 real tables.

Mirrors Telegram _create_rph_word: title, two-column lesson information,
3-column phase/time-activity-notes, and two-column follow-up/reflection.
Does not import the Telegram bot and does not change source lesson content.
"""
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile
from web.telegram_rph_parity import build_layout, clean

WORD = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

def _run(value, *, bold=False, size=17):
    style = (
        '<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial"/>'
        '<w:sz w:val="%d"/>' % size + ("<w:b/>" if bold else "")+"</w:rPr>"
    )
    fragments=[]
    for index,piece in enumerate(str(value or "").split("\n")):
        if index:
            fragments.append("<w:br/>")
        fragments.append('<w:t xml:space="preserve">'+escape(clean(piece))+"</w:t>")
    return "<w:r>"+style+"".join(fragments)+"</w:r>"

def _para(value, *, bold=False, size=17, centered=False, after=0):
    alignment='<w:jc w:val="center"/>' if centered else ""
    return (
        '<w:p><w:pPr><w:spacing w:before="0" w:after="%d" '
        'w:line="200" w:lineRule="auto"/>' % after+alignment+"</w:pPr>"+
        _run(value,bold=bold,size=size)+"</w:p>"
    )

def _cell(value,width,*,bold=False,heading=False):
    # Compact cell padding, black borders, no blue header shading.
    inside=_para(value if value else " ",bold=bold or heading,
                 size=17,centered=heading)
    return (
        '<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>' % width+
        '<w:tcMar><w:top w:w="22" w:type="dxa"/><w:bottom w:w="22" w:type="dxa"/>'
        '<w:left w:w="50" w:type="dxa"/><w:right w:w="50" w:type="dxa"/>'
        '</w:tcMar></w:tcPr>'+inside+"</w:tc>"
    )

def _table(rows,widths,*,head=False):
    total=sum(widths)
    border=''.join('<w:'+x+' w:val="single" w:sz="6" w:color="666666"/>' for x in (
        "top","left","bottom","right","insideH","insideV"))
    table=(
        '<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/>' % total+
        '<w:tblLayout w:type="fixed"/><w:tblBorders>'+border+
        '</w:tblBorders></w:tblPr><w:tblGrid>'+
        ''.join('<w:gridCol w:w="%d"/>'%w for w in widths)+'</w:tblGrid>'
    )
    for index,values in enumerate(rows):
        if len(values)!=len(widths):
            raise ValueError("Incorrect Word table row width")
        is_head=head and index==0
        table += '<w:tr><w:trPr><w:cantSplit/>'+(
            '<w:tblHeader/>' if is_head else "")+'</w:trPr>'
        for j,value in enumerate(values):
            table += _cell(str(value),widths[j],bold=(j==0 and not is_head),
                           heading=is_head)
        table += '</w:tr>'
    return table+'</w:tbl>'

def build_rph_table_docx(data, subject_labels):
    """Build three structural tables from the same data as the browser preview."""
    layout=data.get("telegram_layout") or build_layout(data,subject_labels)
    if layout.get("style")!="telegram-native-rph-v1":
        raise ValueError("Unsupported verified RPH layout")
    head=layout["header"];phases=layout["phases"];footer=layout["footer"]
    if len(head)<16 or len(phases)!=3 or len(footer)!=2:
        raise ValueError("Incomplete source-backed Telegram layout")
    content=[
        _para(layout["title"],bold=True,size=30,centered=True,after=80),
        _table([(row["label"],row["value"]) for row in head],(2950,7700)),
        _para(" ",after=10),
        _table([layout["activity_header"]]+[
            (row["label"],row["activity"],row["notes"])
            for row in phases],(1500,7150,2000),head=True),
        _para(" ",after=10),
        _table([(row["label"],row["value"]) for row in footer],(2950,7700)),
        '<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter1"/>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="425" w:bottom="425" w:left="625" w:right="625" '
        'w:header="180" w:footer="180"/></w:sectPr>',
    ]
    document=(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="'+WORD+'" xmlns:r="'+REL+'"><w:body>'+
        "".join(content)+'</w:body></w:document>'
    )
    footer_xml=(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:ftr xmlns:w="'+WORD+'"><w:p><w:pPr>'
        '<w:jc w:val="center"/></w:pPr>'+_run("CikguLaju AI  •  ",size=15)+
        '<w:r><w:rPr><w:sz w:val="15"/></w:rPr>'
        '<w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>'
    )
    content_types=(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
        '</Types>'
    )
    main_rels=(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="'+REL+'/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )
    document_rels=(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rIdFooter1" Type="'+REL+'/footer" Target="footer1.xml"/>'
        '</Relationships>'
    )
    out=BytesIO()
    with ZipFile(out,"w",ZIP_DEFLATED) as package:
        for name,body in (
            ("[Content_Types].xml",content_types),
            ("_rels/.rels",main_rels),
            ("word/_rels/document.xml.rels",document_rels),
            ("word/document.xml",document),
            ("word/footer1.xml",footer_xml),
        ):
            package.writestr(name,body)
    out.seek(0)
    return out
