"""Private Supabase source for 696 Pendidikan Islam premium RPHs.

Routes and quota handling remain in web.unified_rph_web. The source archive
is in a PRIVATE Storage bucket and never gets a public download URL.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zipfile import ZipFile, BadZipFile

UNIT = "RPH Premium 2027"
YEARS = {2: 112, 3: 147, 4: 151, 5: 143, 6: 143}
BUCKET = "cikgulaju-materials"
OBJECT = "rph-premium/pi-2027/v1/696-word-pdf-bundle.zip"
ZIP_BYTES = 44284495
ZIP_SHA256 = "e19684776c19479f9d5d77e17d5cfc2eececf1b5c4c0e40828b5d9c9f78709c2"


class PrivatePIRPHUnavailable(Exception):
    pass


def valid_pdp(year, lesson):
    if type(year) is not int or year not in YEARS or not isinstance(lesson, (str, int)):
        raise ValueError("Invalid Pendidikan Islam selection")
    raw = str(lesson)
    if not re.fullmatch(r"[1-9][0-9]{0,2}", raw):
        raise ValueError("Invalid PdP")
    n = int(raw)
    if not 1 <= n <= YEARS[year]:
        raise ValueError("Unknown PdP")
    return n


def unit_option(year):
    return [{"value": UNIT, "label": UNIT}] if year in YEARS else []


def pdp_options(year):
    return [{"value": str(n), "label": f"PdP {n:03d}", "pdp_no": n}
            for n in range(1, YEARS.get(year, 0) + 1)]


def _settings(config):
    if not isinstance(config, dict):
        raise PrivatePIRPHUnavailable("Private archive configuration missing")
    base = str(config.get("supabase_url") or "").rstrip("/")
    key = config.get("supabase_key") or ""
    p = urlsplit(base)
    if (p.scheme != "https" or p.hostname != "soxakntcanbycjoygrcx.supabase.co"
            or p.path not in ("", "/") or p.query or p.fragment or p.username or p.password
            or not isinstance(key, str) or len(key) < 30):
        raise PrivatePIRPHUnavailable("Private archive credentials unavailable")
    return base, key


@lru_cache(maxsize=1)
def _verified_zip(base, key):
    url = f"{base}/storage/v1/object/authenticated/{BUCKET}/{OBJECT}"
    headers = {"Authorization": "Bearer " + key, "apikey": key, "Accept": "application/zip"}
    try:
        with urlopen(Request(url, headers=headers, method="GET"), timeout=45) as response:
            if response.status != 200:
                raise PrivatePIRPHUnavailable("Private archive unavailable")
            content = response.read(ZIP_BYTES + 1)
    except OSError as exc:
        raise PrivatePIRPHUnavailable("Private archive unavailable") from exc
    if len(content) != ZIP_BYTES or sha256(content).hexdigest() != ZIP_SHA256:
        raise PrivatePIRPHUnavailable("Private archive integrity mismatch")
    try:
        archive = ZipFile(BytesIO(content))
        if archive.testzip() is not None:
            raise PrivatePIRPHUnavailable("Private archive corrupt")
        return archive
    except (OSError, BadZipFile) as exc:
        raise PrivatePIRPHUnavailable("Private archive corrupt") from exc


def _file(year, n, fmt, config):
    base, key = _settings(config)
    archive = _verified_zip(base, key)
    if fmt not in ("word", "pdf"):
        raise ValueError("Unsupported format")
    extension = "pdf" if fmt == "pdf" else "docx"
    folder = "PDF" if fmt == "pdf" else "DOCX"
    member = (f"Pendidikan_Islam/Tahun_{year}/{folder}/"
              f"CIKGULAJU_RPH_PI_T{year}_PDP{n:03d}.{extension}")
    try:
        data = archive.read(member)
    except KeyError as exc:
        raise PrivatePIRPHUnavailable("RPH missing from verified source") from exc
    if not 1000 <= len(data) <= 10_000_000:
        raise PrivatePIRPHUnavailable("Invalid document size")
    if fmt == "pdf" and not data.startswith(b"%PDF-"):
        raise PrivatePIRPHUnavailable("Invalid native PDF")
    if fmt == "word":
        try:
            with ZipFile(BytesIO(data)) as word:
                if word.testzip() or "word/document.xml" not in word.namelist():
                    raise PrivatePIRPHUnavailable("Invalid Word file")
        except BadZipFile as exc:
            raise PrivatePIRPHUnavailable("Invalid Word file") from exc
    return data


def _metadata_present(teacher):
    return any(str(teacher.get(field) or "").strip()
               for field in ("class", "date", "time", "students", "reflection"))


def _personalize_word(data, teacher):
    """Fill blank fields only; preserve the SK/SP, activities and original content."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    document = Document(BytesIO(data))
    if not document.tables or len(document.tables[0].columns) != 2:
        raise PrivatePIRPHUnavailable("Teacher panel unavailable")
    cell = document.tables[0].cell(0, 1)
    if len(cell.paragraphs) < 4:
        raise PrivatePIRPHUnavailable("Teacher panel incomplete")
    values = [str(teacher.get(k) or "").strip() for k in ("class", "date", "time", "students")]
    for paragraph, value in zip(cell.paragraphs[:4], values):
        if value:
            paragraph.add_run(value).font.name = "Amiri"
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if teacher.get("reflection"):
        last = document.tables[-1]
        if not last.rows or len(last.columns) != 2:
            raise PrivatePIRPHUnavailable("Reflection panel unavailable")
        reflection_cell = last.cell(len(last.rows) - 1, 1)
        if reflection_cell.text.strip():
            raise PrivatePIRPHUnavailable("Original reflection is not blank")
        reflection_cell.paragraphs[0].add_run(
            str(teacher["reflection"]).strip()).font.name = "Amiri"
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _pdf_from_word(word_data):
    converter = shutil.which("libreoffice") or shutil.which("soffice")
    if not converter:
        raise PrivatePIRPHUnavailable("PDF with filled class details unavailable on server")
    with tempfile.TemporaryDirectory(prefix="cikgulaju-pi-") as temp:
        folder = Path(temp)
        source = folder / "rph.docx"
        source.write_bytes(word_data)
        try:
            proc = subprocess.run(
                [converter, "-env:UserInstallation=file://" + str(folder / "profile"),
                 "--headless", "--convert-to", "pdf:writer_pdf_Export",
                 "--outdir", str(folder), str(source)],
                capture_output=True, timeout=35, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PrivatePIRPHUnavailable("PDF conversion unavailable") from exc
        output = folder / "rph.pdf"
        if proc.returncode != 0 or not output.is_file():
            raise PrivatePIRPHUnavailable("PDF conversion failed")
        data = output.read_bytes()
        if not 1000 <= len(data) <= 10_000_000 or not data.startswith(b"%PDF-"):
            raise PrivatePIRPHUnavailable("Invalid converted PDF")
        return data


def request_private_document(year, lesson, fmt, teacher, config):
    n = valid_pdp(year, lesson)
    if fmt not in ("word", "pdf") or not isinstance(teacher, dict):
        raise ValueError("Invalid private RPH request")
    if not _metadata_present(teacher):
        return BytesIO(_file(year, n, fmt, config))
    if fmt == "pdf":
        # Preserve original PDF geometry; only fill its existing blank cells.
        return BytesIO(_fill_pdf_fields(_file(year, n, "pdf", config), teacher))
    word = _personalize_word(_file(year, n, "word", config), teacher)
    return BytesIO(word)


def _fill_pdf_fields(data, teacher):
    """Fill four consistently positioned blank Jawi header cells in original PDF."""
    try:
        import fitz
        document = fitz.open(stream=data, filetype="pdf")
        page = document[0]
        values = [str(teacher.get(k) or "").strip()
                  for k in ("class", "date", "time", "students")]
        # Original Jawi labels start at (38, 20.5); only unused metadata
        # cells are written. Never obscure the lesson title or SK/SP.
        font = "helv"
        font_file = Path(__file__).resolve().parents[1] / "fonts/jawi/Amiri-Regular.ttf"
        if font_file.is_file():
            page.insert_font(fontname="amiri", fontfile=str(font_file))
            font = "amiri"
        for index, value in enumerate(values):
            if not value:
                continue
            top = 24 + (20.7 * index)
            rect = fitz.Rect(91, top, 213, top + 17)
            remaining = page.insert_textbox(rect, value, fontsize=9, fontname=font)
            if remaining < 0:
                raise PrivatePIRPHUnavailable("Teacher detail too long for existing box")
        reflection = str(teacher.get("reflection") or "").strip()
        if reflection:
            labels = [
                span
                for block in page.get_text("dict")["blocks"]
                for line in block.get("lines", ())
                for span in line.get("spans", ())
                if "رفليكسي" in span["text"] or "رفليکسي" in span["text"]
            ]
            if not labels:
                raise PrivatePIRPHUnavailable("Reflection panel unavailable")
            top = float(labels[-1]["bbox"][1]) + 2
            rect = fitz.Rect(38, top, 430, min(top + 35, page.rect.y1 - 20))
            if rect.height < 12 or page.insert_textbox(
                    rect, reflection, fontsize=8, fontname=font) < 0:
                raise PrivatePIRPHUnavailable("Manual reflection too long for the available box")
        return document.tobytes(garbage=3, deflate=True)
    except PrivatePIRPHUnavailable:
        raise
    except Exception as exc:
        raise PrivatePIRPHUnavailable("Unable to fill the original PDF safely") from exc
