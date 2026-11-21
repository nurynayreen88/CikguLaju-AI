"""Private Supabase source for 696 Pendidikan Islam premium RPHs.

Routes and quota handling remain in web.unified_rph_web. The source archive
is in a PRIVATE Storage bucket and never gets a public download URL.
"""
from __future__ import annotations

from functools import lru_cache
import os
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
ARCHIVES = {
    "v1": {
        "object": "rph-premium/pi-2027/v1/696-word-pdf-bundle.zip",
        "bytes": 44284495,
        "sha256": "e19684776c19479f9d5d77e17d5cfc2eececf1b5c4c0e40828b5d9c9f78709c2",
    },
    "v2": {
        "object": "rph-premium/pi-2027/v2/696-word-pdf-bundle.zip",
        "bytes": 49779272,
        "sha256": "f68807065178f15e2acb4dd25caa7f179cad33a02d186327ec89515c9ae10569",
    },
}
# PDF-only additive archive for all 696 v2 RPH: Amiri-Bold activity
# headings re-rendered from their original Jawi Word templates.
# SHA-256 checked before any user receives a file.
ARCHIVES["v2-bold-pdf"] = {
    "object": "rph-premium/pi-2027/v2/696-jawi-bold-pdf-addon.zip",
    "bytes": 26641162,
    "sha256": "4387c6808a286fb6855bdb5f48e43a4436ef7264e0b9e916c7067a99f217937d",
}
# v2 remains OFF until the new private Storage object exists and is verified.
# Old v1 remains intact for safe rollback. Never expose a signed Drive URL.
V2_FLAG = "CIKGULAJU_PI_LOGIN_V2_ENABLED"


def _edition():
    return "v2" if os.environ.get(V2_FLAG, "").strip() == "1" else "v1"


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
    return [{"value": UNIT, "label": "Senarai PdP"}] if year in YEARS else []


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


@lru_cache(maxsize=2)
def _verified_zip(base, key, edition):
    if edition not in ARCHIVES:
        raise PrivatePIRPHUnavailable("Unsupported private archive edition")
    source = ARCHIVES[edition]
    url = f"{base}/storage/v1/object/authenticated/{BUCKET}/{source['object']}"
    headers = {"Authorization": "Bearer " + key, "apikey": key, "Accept": "application/zip"}
    try:
        with urlopen(Request(url, headers=headers, method="GET"), timeout=45) as response:
            if response.status != 200:
                raise PrivatePIRPHUnavailable("Private archive unavailable")
            content = response.read(source["bytes"] + 1)
    except OSError as exc:
        raise PrivatePIRPHUnavailable("Private archive unavailable") from exc
    if len(content) != source["bytes"] or sha256(content).hexdigest() != source["sha256"]:
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
    if fmt not in ("word", "pdf"):
        raise ValueError("Unsupported format")
    # Never serve the old non-bold archived PDF when v2 is active.
    # Word source remains v2, with complex-script bold applied below.
    edition = "v2-bold-pdf" if fmt == "pdf" and _edition() == "v2" else _edition()
    archive = _verified_zip(base, key, edition)
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


def _rtl_safe_value(value):
    # Existing template paragraphs are RTL. LRM preserves the exact order
    # of Roman class names, ISO dates, times and Roman-language reflections.
    # Jawi remains genuine RTL and is never reversed or transliterated.
    return value if _is_jawi(value) else "\u200e" + value + "\u200e"


def _personalize_word(data, teacher):
    """Fill blank fields only; preserve the SK/SP, activities and original content."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    document = Document(BytesIO(data))
    if not document.tables or len(document.tables[0].columns) != 2:
        raise PrivatePIRPHUnavailable("Teacher panel unavailable")
    cell = document.tables[0].cell(0, 1)
    values = [str(teacher.get(k) or "").strip() for k in ("class", "date", "time", "students")]
    if cell.tables:
        # Approved login example: title + LEFT teacher grid, four labeled
        # rows, each with a genuinely empty value cell. Never append to labels.
        grid = cell.tables[0]
        if len(grid.rows) != 4 or len(grid.columns) != 2:
            raise PrivatePIRPHUnavailable("Approved teacher grid incomplete")
        targets = [row.cells[1].paragraphs[0] for row in grid.rows]
        if any(row.cells[1].text.strip() for row in grid.rows):
            raise PrivatePIRPHUnavailable("Original teacher values are not blank")
    else:
        # Existing v1 RPH teacher labels and values share four paragraphs.
        if len(cell.paragraphs) < 4:
            raise PrivatePIRPHUnavailable("Teacher panel incomplete")
        targets = list(cell.paragraphs[:4])
    for paragraph, value in zip(targets, values):
        if value:
            paragraph.add_run(_rtl_safe_value(value)).font.name = "Amiri"
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if teacher.get("reflection"):
        last = document.tables[-1]
        if not last.rows or len(last.columns) != 2:
            raise PrivatePIRPHUnavailable("Reflection panel unavailable")
        reflection_cell = last.cell(len(last.rows) - 1, 1)
        if reflection_cell.text.strip():
            raise PrivatePIRPHUnavailable("Original reflection is not blank")
        reflection_cell.paragraphs[0].add_run(
            _rtl_safe_value(str(teacher["reflection"]).strip())).font.name = "Amiri"
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
    personalized = _metadata_present(teacher)
    # All 696 PDFs are pre-rendered and audited from the approved Word
    # source with Amiri-Bold (no LibreOffice/slow conversion on live Web).
    if fmt == "pdf":
        pdf = _file(year, n, "pdf", config)
        return BytesIO(_fill_pdf_fields(pdf, teacher, edition=_edition())
                       if personalized else pdf)
    word = _file(year, n, "word", config)
    if _edition() == "v2":
        from web.pi_696_jawi_pdf_fix import with_jawi_bold
        word, _ = with_jawi_bold(word)
    return BytesIO(_personalize_word(word, teacher) if personalized else word)

@lru_cache(maxsize=1)
def _amiri_bytes():
    """Fetch only the original open-source Amiri font for private server rendering.

    Font bytes are never sent to users or exposed in public Storage.
    """
    candidate = Path(__file__).resolve().parents[1] / "fonts/jawi/Amiri-Regular.ttf"
    if candidate.is_file():
        data = candidate.read_bytes()
    else:
        url = "https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Regular.ttf"
        with urlopen(Request(url, headers={"User-Agent": "CikguLaju-RPH/1"}),
                     timeout=18) as response:
            data = response.read(2_000_001)
    if not 10_000 <= len(data) <= 2_000_000 or data[:4] not in (
            b"\x00\x01\x00\x00", b"true"):
        raise PrivatePIRPHUnavailable("Fon Jawi belum boleh dimuatkan")
    return data


def _is_jawi(value):
    return any("\u0600" <= ch <= "\u08ff" for ch in value)


def _draw_shaped_jawi(page, rect, value):
    """Use PyMuPDF Story/HTML shaping, never raw insert_textbox for RTL Jawi."""
    from html import escape as escape_html
    import fitz

    font = _amiri_bytes()
    with tempfile.TemporaryDirectory(prefix="cikgulaju-amiri-") as temporary:
        path = Path(temporary)
        (path / "Amiri-Regular.ttf").write_bytes(font)
        css = (
            "@font-face {font-family: Amiri;"
            "src: url('Amiri-Regular.ttf');}"
            "html,body,div {font-family: Amiri;font-size:9pt;line-height:10pt;"
            "direction:rtl;text-align:right;margin:0;padding:0;}"
        )
        story = fitz.Story(
            html='<div dir="rtl" lang="ms-Arab">' + escape_html(value) + "</div>",
            user_css=css, archive=fitz.Archive(str(path))
        )
        overlay = BytesIO()
        writer = fitz.DocumentWriter(overlay)
        dev = writer.begin_page(page.rect)
        placed = story.place(rect)
        if placed[0] != 0:
            writer.end_page()
            writer.close()
            raise PrivatePIRPHUnavailable("Catatan Jawi terlalu panjang untuk kotak")
        story.draw(dev)
        writer.end_page()
        writer.close()
        with fitz.open(stream=overlay.getvalue(), filetype="pdf") as extra:
            page.show_pdf_page(page.rect, extra, 0, overlay=True)


def _fill_pdf_fields(data, teacher, *, edition="v1"):
    """Fill only existing blank boxes; v1 and owner-approved v2 differ."""
    try:
        import fitz
        document = fitz.open(stream=data, filetype="pdf")
        page = document[0]
        values = [str(teacher.get(k) or "").strip()
                  for k in ("class", "date", "time", "students")]
        for index, value in enumerate(values):
            if not value:
                continue
            if edition == "v2":
                # Approved RTL header: original Jawi labels are on the RIGHT.
                # Place only in the empty value cells at the LEFT.
                # Verified against the real one-page v2 PDF: teacher grid
                # borders at y=41.95,63.8,85.6,107.4,129.35 points.
                top = 44 + (21.82 * index)
                rect = fitz.Rect(39, top, 122.5, top + 18)
            elif edition == "v1":
                top = 24 + (20.7 * index)
                rect = fitz.Rect(91, top, 213, top + 17)
            else:
                raise PrivatePIRPHUnavailable("Unsupported PDF template edition")
            if _is_jawi(value):
                _draw_shaped_jawi(page, rect, value)
            elif page.insert_textbox(rect, value, fontsize=9, fontname="helv") < 0:
                raise PrivatePIRPHUnavailable("Maklumat guru terlalu panjang untuk kotak")
        reflection = str(teacher.get("reflection") or "").strip()
        if reflection:
            labels = [
                span for block in page.get_text("dict")["blocks"]
                for line in block.get("lines", ())
                for span in line.get("spans", ())
                if "رفليكسي" in span["text"] or "رفليکسي" in span["text"]
            ]
            if not labels:
                raise PrivatePIRPHUnavailable("Kotak refleksi tiada dalam RPH sumber")
            top = float(labels[-1]["bbox"][1]) + (7 if edition == "v2" else 2)
            bottom = (top + 19 if edition == "v2" else min(top + 35, page.rect.y1 - 20))
            rect = fitz.Rect(38, top, 430, bottom)
            if rect.height < 12:
                raise PrivatePIRPHUnavailable("Kotak refleksi tidak mencukupi")
            if _is_jawi(reflection):
                _draw_shaped_jawi(page, rect, reflection)
            elif page.insert_textbox(rect, reflection, fontsize=7.1 if edition == "v2" else 8,
                                     fontname="helv") < 0:
                raise PrivatePIRPHUnavailable("Refleksi terlalu panjang untuk kotak")
        return document.tobytes(garbage=3, deflate=True)
    except PrivatePIRPHUnavailable:
        raise
    except Exception as exc:
        raise PrivatePIRPHUnavailable("PDF tidak dapat diisi dengan selamat") from exc
