"""Read name/code columns from bounded, ordinary XLSX worksheets."""
import posixpath
import re
from xml.etree import ElementTree as ET

MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
DOC_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PACKAGE_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
CELL = re.compile(r"([A-Z]{1,3})[1-9][0-9]*")


def xml(archive, name):
    content = archive.read(name).decode("utf-8-sig")
    if re.search(r"<!\s*(DOCTYPE|ENTITY)", content, re.I):
        raise ValueError("Unsafe XML declaration")
    return ET.fromstring(content)


def read_rows(archive):
    workbook = xml(archive, "xl/workbook.xml")
    sheets = workbook.findall(f"{MAIN}sheets/{MAIN}sheet")
    visible = [sheet for sheet in sheets if sheet.get("state", "visible") == "visible"]
    if not visible:
        raise ValueError("No visible worksheets")
    sheet = next((s for s in visible if s.get("name") == "Senarai Murid"), visible[0])
    relationships = xml(archive, "xl/_rels/workbook.xml.rels")
    rel = next((r for r in relationships.findall(f"{PACKAGE_REL}Relationship")
                if r.get("Id") == sheet.get(DOC_REL + "id")), None)
    if rel is None or rel.get("TargetMode") == "External":
        raise ValueError("Invalid worksheet link")
    target = rel.get("Target", "")
    member = posixpath.normpath(target.lstrip("/") if target.startswith("/") else "xl/" + target)
    if not member.startswith("xl/worksheets/") or not member.endswith(".xml"):
        raise ValueError("Invalid worksheet path")
    strings = []
    if "xl/sharedStrings.xml" in archive.namelist():
        table = xml(archive, "xl/sharedStrings.xml")
        strings = [plain(item) for item in table.findall(f"{MAIN}si")]
    data = xml(archive, member)
    for row in data.iterfind(f"{MAIN}sheetData/{MAIN}row"):
        values = [""] * 60
        for cell in row.findall(MAIN + "c"):
            match = CELL.fullmatch(cell.get("r", ""))
            if not match:
                continue
            column = 0
            for letter in match.group(1):
                column = 26 * column + ord(letter) - ord("A") + 1
            if column > 60:
                continue
            mode = cell.get("t")
            value = cell.findtext(MAIN + "v", default="")
            if cell.find(MAIN + "f") is not None:
                value = "="
            elif mode == "s":
                offset = int(value)
                if not 0 <= offset < len(strings):
                    raise ValueError("Invalid shared string")
                value = strings[offset]
            elif mode == "inlineStr":
                inline = cell.find(MAIN + "is")
                value = plain(inline) if inline is not None else ""
            values[column - 1] = value
        yield values


def plain(item):
    direct = item.findtext(MAIN + "t", default="")
    rich = "".join(run.findtext(MAIN + "t", default="") for run in item.findall(MAIN + "r"))
    return direct + rich
