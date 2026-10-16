"""Private all-year PJPK preview renderer; never production RPH."""
from pathlib import Path
import csv
import io
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from html import escape as html_escape
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from pypdf import PdfReader
from pjpk_private_menu import ensure_menu_view
from pjpk_rph_engine import generate

ROOT = Path(__file__).resolve().parent
DB = ROOT / "pjpk_candidate.db"
with (ROOT / "COLLISION_QUARANTINE_10.csv").open(encoding="utf-8-sig", newline="") as _f:
    QUARANTINE = {int(row["entry_id"]) for row in csv.DictReader(_f)}
assert len(QUARANTINE) == 10, "Fail closed: quarantine file invalid"

def _require_preview_eligible(entry_id):
    if int(entry_id) in QUARANTINE:
        raise ValueError("Duplicate topic/SP quarantined")
    with sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True) as con:
        ensure_menu_view(con)
        row = con.execute(
            "SELECT entry_status FROM pjpk_v26_30_candidate_menu WHERE entry_id=?",
            (int(entry_id),)
        ).fetchone()
    if not row or row[0] != "REVIEW_ONLY":
        raise ValueError("Entry blocked or unknown")

def home():
    with sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True) as con:
        ensure_menu_view(con)
        rows = con.execute(
            "SELECT entry_id,year,component,topic,entry_status "
            "FROM pjpk_v26_30_candidate_menu WHERE entry_status='REVIEW_ONLY' "
            "ORDER BY year,component,sequence_no"
        ).fetchall()
    rows = [row for row in rows if row[0] not in QUARANTINE]
    items = "".join(
        f"<div>Tahun {year} {component} — {html_escape(topic or '')} "
        f"<small>{status}</small> <a href='/preview/{entry_id}'>Lihat draf</a> "
        f"<a href='/pdf/{entry_id}'>PDF</a></div>"
        for entry_id, year, component, topic, status in rows
    )
    return (
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>PJPK Preview</title>'
        '<style>body{font:16px system-ui;max-width:800px;margin:auto;padding:20px}'
        'a{display:inline-block;padding:8px}small{color:#666}</style>'
        '<h2>Pratonton PJPK (BUKAN PRODUKSI)</h2>'
        '<p>Semua data asal kekal. Anchor/konflik disekat oleh enjin.</p>' + items
    )

def get_text(entry_id):
    _require_preview_eligible(entry_id)
    try:
        return generate(str(DB), int(entry_id), mode="preview")
    except (ValueError, sqlite3.Error) as exc:
        raise ValueError(str(exc))

def pdf(entry_id):
    content = get_text(entry_id)
    # Adaptive typography only; never truncate curriculum or activity text.
    for font_size, leading, space, margin in [
        (10, 13, 7, 42), (9.5, 12, 5, 38), (9, 11, 4, 34),
        (8.5, 10, 3, 30), (8, 9.5, 2, 28)
    ]:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, leftMargin=margin, rightMargin=margin,
            topMargin=margin, bottomMargin=margin
        )
        styles = getSampleStyleSheet()
        title = ParagraphStyle(
            "DraftTitleAdaptive", parent=styles["Heading2"], fontSize=font_size + 2,
            leading=leading + 2, textColor=colors.darkred, alignment=TA_CENTER,
            spaceAfter=space
        )
        body = ParagraphStyle(
            "DraftBodyAdaptive", parent=styles["BodyText"], fontSize=font_size,
            leading=leading, spaceAfter=space, allowWidows=0, allowOrphans=0
        )
        story = [Paragraph("DRAF PRATONTON — BELUM DILULUSKAN", title)]
        for paragraph in content.split("\n\n"):
            if paragraph.strip():
                story.append(Paragraph(escape(paragraph).replace("\n", "<br/>"), body))
        doc.build(story)
        if len(PdfReader(io.BytesIO(buffer.getvalue())).pages) == 1:
            return buffer.getvalue()
    raise ValueError("Draft exceeds one page at minimum readable preview typography; manual layout review required")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/":
                payload, mime = home().encode("utf-8"), "text/html; charset=utf-8"
            elif path.startswith("/preview/"):
                payload, mime = get_text(int(path.split("/")[-1])).encode("utf-8"), "text/plain; charset=utf-8"
            elif path.startswith("/pdf/"):
                payload, mime = pdf(int(path.split("/")[-1])), "application/pdf"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (ValueError, sqlite3.Error) as exc:
            self.send_error(403, str(exc))

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 5055), Handler).serve_forever()
