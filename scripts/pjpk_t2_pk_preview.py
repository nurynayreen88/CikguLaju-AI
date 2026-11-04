"""Render all eighteen T2 PK editorial records as clearly watermarked A4 HTML previews.

No curriculum fields are inferred. Missing verified standards, page and RPT slot
are shown as pending. Never writes to the production database.
Run: python -m scripts.pjpk_t2_pk_preview OUTPUT_DIRECTORY
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "docs/pjpk/T2_PK_7_COMPLETE_RPH_EDITORIAL_STAGING_20261024.json",
    ROOT / "docs/pjpk/T2_PK_11_REMAINING_EDITORIAL_STAGING_20261024.json",
)
CSS = """@page { size: A4; margin: 12mm 13mm; }
body { font-family: sans-serif; font-size: 9pt; line-height: 1.27; color: #17212b; }
h1 { font-size: 13pt; text-align: center; margin: 0 0 6px; }
h2 { font-size: 9pt; margin: 7px 0 2px; border-bottom: 1px solid #777; }
p { margin: 3px 0; }
.meta { font-size: 8pt; border: 1px solid #888; padding: 5px; }
.warn { font-size: 8pt; font-weight: bold; border: 2px solid #a33; padding: 4px; text-align: center; }
section { break-inside: avoid; }
"""


def esc(value):
    return html.escape(str(value), quote=True)


def section(title, body):
    return f"<section><h2>{esc(title)}</h2><p>{esc(body)}</p></section>"


def render(record):
    if record.get("production_ready") is not False:
        raise ValueError(f"{record['id']}: preview requires blocked production status")
    activities = record["activities"]
    if len(activities) != 2:
        raise ValueError(f"{record['id']}: expected two substantive activities")
    sp = ", ".join(record.get("sp") or []) or "Belum disahkan"
    sp += " (teks SP belum disahkan)"
    blocks = [
        '<h1>RANCANGAN PENGAJARAN HARIAN</h1>',
        '<div class="warn">DRAF EDITORIAL — BELUM DILULUSKAN UNTUK PRODUKSI</div>',
        f'<div class="meta"><b>Tahun:</b> 2 | <b>Subjek:</b> Pendidikan Kesihatan | <b>ID:</b> {esc(record["id"])}<p><b>Tajuk:</b> {esc(record["topic"])}</p><p><b>SK:</b> Belum disahkan | <b>SP:</b> {esc(sp)}</p><p><b>Slot RPT / Halaman buku teks:</b> Belum disahkan</p><p><b>Tarikh / Masa / Kelas:</b> Diisi guru</p></div>',
        section("Objektif:", record["objective"]),
        section("BBM:", record["materials"]),
        section("Set Induksi", record["induction"]),
    ]
    for n, activity in enumerate(activities, 1):
        blocks.append(section(f"Aktiviti {n} – {activity['heading']}", activity["body"]))
    blocks += [
        section("Pengukuhan / Penilaian", record["reinforcement"]),
        section("Penutup", record["closure"]),
        section("Pentaksiran:", record["assessment"]),
        section("Rujukan:", "Inventori sumber PJPK Tahun 2 PK; padanan DSKP, RPT dan buku teks menunggu semakan bukti tepat."),
        section("Refleksi:", "Diisi oleh guru selepas PdP."),
    ]
    return '<!doctype html><html lang="ms"><head><meta charset="utf-8"><style>' + CSS + '</style></head><body>' + "".join(blocks) + "</body></html>"


def generate(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    records = [record for path in SOURCES for record in json.loads(path.read_text(encoding="utf-8"))["records"]]
    ids = [r["id"] for r in records]
    if len(records) != 18 or len(ids) != len(set(ids)):
        raise ValueError("Expected eighteen unique T2 PK editorial records")
    for record in records:
        (output / f"T2_PK_{record['id']}.html").write_text(render(record), encoding="utf-8")
    return len(records)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m scripts.pjpk_t2_pk_preview OUTPUT_DIRECTORY")
    print(f"Generated {generate(sys.argv[1])} watermarked T2 PK editorial HTML previews")
