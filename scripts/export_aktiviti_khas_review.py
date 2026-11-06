"""Export verified special-activity RPH draft samples for human review.

Produces one ZIP: 59 DOCX, 59 PDF, immutable manifest and review notes.
The archive is NOT a production release or user entitlement bypass.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pypdf import PdfReader
from rph_standalone.aktiviti_khas.engine import _catalog, render


EXAMPLE_TEACHER = {
    "class": "Kelas Contoh",
    "date": "2026-11-06",
    "time": "08:00-09:00",
    "students": "30",
}
NOTICE = """CIKGULAJU - RPH AKTIVITI KHAS (DRAF SAHAJA)

Pakej ini untuk semakan guru/pembangun, bukan bahan rasmi KPM.
RPH Transisi hanya Tahun 1; Tamat Sukatan menggunakan 13 subjek
dengan variasi Tahun 1-2, 3-4, 5-6.

Setiap PDF dan Word disediakan daripada sumber katalog GitHub yang sama.
59 dokumen Word dan 59 dokumen PDF termasuk dalam fail ini.
Jangan serahkan kepada pengguna produksi sebelum lulus semakan pedagogi,
ujian akses, kuota, integrasi Telegram/Web dan pengesahan penerbitan.
Tiada SK/SP rasmi dipadankan secara automatik.

Rujuk MANIFEST.json bagi sumber, ID, subjek dan SHA-256 fail.
"""


def _slug(text):
    value = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")
    if not value or len(value) > 90:
        raise ValueError("Unsafe archive segment")
    return value


def export(path):
    payload, digest = _catalog()
    if payload["release_status"] != "DRAFT_REVIEW":
        raise ValueError("Review exporter only accepts an explicitly draft catalogue")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    seen = set()
    with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for row in payload["activities"]:
            year = row["years"][0]
            subject = row.get("subject_options", [None])[0]
            kind = row["category"]
            tier = ("Tahun_1_Transisi" if kind == "TRANSISI_TAHUN_1"
                    else "Tamat_Sukatan/" + _slug(subject)
                    + "/Tahun_" + str(row["years"][0]) + "-" + str(row["years"][-1]))
            stem = row["id"] + "_" + _slug(row["title"]) + "_DRAF"
            info = {
                "activity_id": row["id"],
                "title": row["title"],
                "category": kind,
                "years": row["years"],
                "subject": subject,
                "phase": row["phase"],
                "documents": [],
            }
            for fmt, ext in (("word", ".docx"), ("pdf", ".pdf")):
                body = render(row, year, EXAMPLE_TEACHER, fmt, subject=subject)
                if not isinstance(body, bytes) or len(body) < 900:
                    raise ValueError("Empty review document: " + row["id"])
                if fmt == "pdf":
                    reader = PdfReader(io.BytesIO(body))
                    if len(reader.pages) != 1:
                        raise ValueError("Not one-page PDF: " + row["id"])
                    if not body.startswith(b"%PDF-"):
                        raise ValueError("Invalid PDF: " + row["id"])
                else:
                    if not body.startswith(b"PK"):
                        raise ValueError("Invalid DOCX: " + row["id"])
                name = tier + "/" + stem + ext
                if name in seen:
                    raise ValueError("Duplicate review output")
                seen.add(name)
                archive.writestr(name, body)
                info["documents"].append({
                    "format": fmt,
                    "archive_path": name,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                })
            records.append(info)
        if len(records) != 59 or len(seen) != 118:
            raise ValueError("Incomplete review inventory")
        manifest = {
            "status": "DRAFT_REVIEW",
            "catalogue_sha256": digest,
            "document_count": 118,
            "rph_count": 59,
            "example_teacher": EXAMPLE_TEACHER,
            "records": records,
        }
        archive.writestr("MANIFEST.json", json.dumps(
            manifest, indent=2, ensure_ascii=False) + "\n")
        archive.writestr("BACA_DAHULU.txt", NOTICE)
    print("PASS: 59 Word + 59 PDF in", path, "bytes", path.stat().st_size)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/CikguLaju_59_RPH_Aktiviti_Khas_DRAF.zip")
    args = parser.parse_args()
    export(args.output)


if __name__ == "__main__":
    main()
