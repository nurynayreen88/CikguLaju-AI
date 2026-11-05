"""Compact A4 Word RPH layout with real bordered tables, not text-only paragraphs.

Pure OOXML; no additional runtime dependencies or changes to the Telegram renderer.
Source Markdown stays unchanged and every field from the verified Web preview
is preserved inside table rows. The table structure is used for all Web RPH
subjects with a source, not just English.
"""
from io import BytesIO
import re
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


def _clean(value):
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(value))
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    return re.sub(r"(?m)^\s*[-*]\s+", "• ", value).strip()


def _paragraph(value, *, bold=False, size=16, color="203A4A", after=14):
    text = escape(_clean(value))
    props = (
        '<w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos" '
        'w:eastAsia="Aptos"/><w:sz w:val="%d"/>' % size
        + ('<w:b/>' if bold else '')
        + '<w:color w:val="%s"/></w:rPr>' % color
    )
    return (
        '<w:p><w:pPr><w:spacing w:before="0" w:after="%d" '
        'w:line="198" w:lineRule="auto"/></w:pPr>' % after
        + '<w:r>' + props + '<w:t xml:space="preserve">'
        + text + '</w:t></w:r></w:p>'
    )


def _cell(value, width, *, colored=False, bold=False):
    color = '1D3448' if colored else 'FFFFFF'
    shading = 'E5F1F7' if colored else 'FFFFFF'
    parts = [x.strip() for x in str(value).splitlines() if x.strip()]
    if not parts:
        parts = ["—"]
    content = ''.join(
        _paragraph(piece, bold=bold, size=16 if colored else 16, color=color)
        for piece in parts
    )
    return (
        '<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>' % width
        + '<w:shd w:fill="' + shading + '"/>'
        + '<w:tcMar><w:top w:w="56" w:type="dxa"/><w:left w:w="75" w:type="dxa"/>'
        + '<w:bottom w:w="40" w:type="dxa"/><w:right w:w="75" w:type="dxa"/></w:tcMar>'
        + '</w:tcPr>' + content + '</w:tc>'
    )


def _row(label, value, *, heading=False):
    return (
        '<w:tr><w:trPr>' + ('<w:tblHeader/>' if heading else '') + '</w:trPr>'
        + _cell(label, 2330, colored=True, bold=True)
        + _cell(value, 8370, colored=heading, bold=heading)
        + '</w:tr>'
    )


def build_rph_table_docx(data, subject_labels):
    """Return a Word file with real table grid and untouched lesson-specific content."""
    if not isinstance(data, dict) or not isinstance(data.get("fields"), list):
        raise ValueError("RPH fields unavailable")
    subject = subject_labels[data["subject"]]
    year = int(data["year"])
    teacher = data.get("teacher") or {}
    title = '%s — %s %d | %s' % (
        subject, "Year" if data["subject"] == "ENGLISH" else "Tahun",
        year, str(data["title"])
    )
    content = [
        _paragraph("CIKGULAJU AI  |  RANCANGAN PENGAJARAN HARIAN",
                   bold=True, size=22, color="164267", after=80),
        _paragraph(title, bold=True, size=18, after=70),
    ]
    rows = [
        _row("Maklumat", "RPH & pelaksanaan PdP", heading=True),
        _row("Kelas", teacher.get("class") or "________________"),
        _row("Tarikh", teacher.get("date") or "________________"),
        _row("Masa", teacher.get("time") or "________________"),
        _row("Status sumber", str(data.get("status") or "Semakan guru")),
    ]
    for field in data["fields"]:
        label, value = field.get("label"), field.get("value")
        if isinstance(label, str) and isinstance(value, str) and label.strip() and value.strip():
            rows.append(_row(label.strip(), value))
    if len(rows) <= 5:
        raise ValueError("Missing RPH content")
    border = '<w:top/><w:left/><w:bottom/><w:right/><w:insideH/><w:insideV/>'
    table = (
        '<w:tbl><w:tblPr><w:tblW w:w="10700" w:type="dxa"/>'
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblBorders>' + border.replace('/>', ' w:val="single" w:sz="4" w:color="91ABC1"/>')
        + '</w:tblBorders></w:tblPr>'
        '<w:tblGrid><w:gridCol w:w="2330"/><w:gridCol w:w="8370"/></w:tblGrid>'
        + ''.join(rows) + '</w:tbl>'
    )
    content.append(table)
    content.append(_paragraph(str(data.get("notice") or ""), size=14, color="53636F", after=0))
    content.append(
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="500" w:right="580" w:bottom="500" w:left="580" '
        'w:header="300" w:footer="300"/></w:sectPr>'
    )
    document = (
        '<?xml version="1.0" encoding="utf-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>' + ''.join(content) + '</w:body></w:document>'
    )
    manifest = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/></Relationships>'
    )
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", manifest)
        package.writestr("_rels/.rels", rels)
        package.writestr("word/document.xml", document)
    output.seek(0)
    return output
