"""Render private PJPK draft PDFs for QA; no DB writes, deployment or AI calls."""
import argparse
import csv
import hashlib
import re
import sqlite3
from pathlib import Path

from pypdf import PdfReader
from preview_server import DB, QUARANTINE, pdf
from pjpk_private_menu import ensure_menu_view


def safe_name(value):
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "")).strip("_")
    return value[:70] or "topik"


def render_all(outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True) as con:
        ensure_menu_view(con)
        rows = con.execute(
            "SELECT entry_id,year,component,topic,entry_status "
            "FROM pjpk_v26_30_candidate_menu WHERE entry_status='REVIEW_ONLY' "
            "ORDER BY year,component,sequence_no"
        ).fetchall()
    rows = [row for row in rows if int(row[0]) not in QUARANTINE]
    manifest = []
    failures = []
    for entry_id, year, component, topic, status in rows:
        filename = f"Tahun_{year}_{safe_name(component)}_{safe_name(topic)}_{entry_id}.pdf"
        target = outdir / filename
        try:
            payload = pdf(int(entry_id))
            reader = PdfReader(__import__("io").BytesIO(payload))
            if len(reader.pages) != 1:
                raise ValueError(f"expected 1 A4 page, got {len(reader.pages)}")
            page_text = reader.pages[0].extract_text() or ""
            if "DRAF PRATONTON" not in page_text or "BELUM DILULUSKAN" not in page_text:
                raise ValueError("draft disclaimer missing")
            target.write_bytes(payload)
            manifest.append({
                "entry_id": entry_id, "year": year, "component": component,
                "topic": topic, "entry_status": status, "pdf_file": filename,
                "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                "document_status": "DRAF_PRATONTON_BELUM_DILULUSKAN",
            })
        except Exception as exc:
            failures.append({"entry_id": entry_id, "year": year, "component": component, "topic": topic, "error": str(exc)})
    with (outdir / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "entry_id", "year", "component", "topic", "entry_status",
            "pdf_file", "bytes", "sha256", "document_status"
        ])
        writer.writeheader()
        writer.writerows(manifest)
    with (outdir / "render_failures.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["entry_id", "year", "component", "topic", "error"])
        writer.writeheader()
        writer.writerows(failures)
    total_bytes = sum(row["bytes"] for row in manifest)
    print(f"eligible={len(rows)} rendered={len(manifest)} failed={len(failures)} total_pdf_bytes={total_bytes}")
    print(f"manifest={outdir / 'manifest.csv'}")
    if failures or len(manifest) != len(rows):
        raise SystemExit(1)
    print("PASS: all private draft PDFs are one-page A4 with draft disclaimer; no DB writes")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="artifacts/pjpk_draft_pdfs_v2678")
    args = parser.parse_args()
    render_all(args.outdir)


if __name__ == "__main__":
    main()
