"""Render complete editorial PJPK RPH as printable A4 HTML (preview only).

Uses stored activities verbatim. No AI, database mutation, release flag change or deployment.
"""
import html
import json
from pathlib import Path
from scripts.pjpk_t5_complete_rph_audit import JSON_PATH, audit

def esc(value):
    return html.escape(str(value or ""), quote=True)

def render(row, teacher=None):
    if row.get("production_ready") is not False or row.get("status") != "editorial_staging_only":
        raise ValueError("Only reviewed editorial staging records may be previewed")
    teacher = teacher or {}
    allowed = {"date", "day", "class", "time", "duration_minutes", "reflection"}
    if set(teacher) - allowed:
        raise ValueError("Unsupported teacher field")
    if any(not isinstance(value, (str, int, type(None))) for value in teacher.values()):
        raise ValueError("Invalid teacher field value")
    cells = [("Tarikh", teacher.get("date")), ("Hari", teacher.get("day")),
             ("Kelas", teacher.get("class")), ("Masa", teacher.get("time")),
             ("Tempoh (minit)", teacher.get("duration_minutes"))]
    meta = "".join(f"<span><b>{esc(k)}:</b> {esc(v) if v is not None else '____________'}</span>" for k,v in cells)
    activities = "".join(f"<section><h3>{esc(a['heading'])}</h3><p>{esc(a['body'])}</p></section>"
                         for a in row["activities"])
    reflection = teacher.get("reflection")
    return f"""<!doctype html><html lang="ms"><head><meta charset="utf-8">
<title>RPH {esc(row['id'])} — {esc(row['topic'])}</title>
<style>
@page {{size:A4 portrait;margin:11mm 12mm}}
*{{box-sizing:border-box}}body{{font-family:Arial,sans-serif;color:#111;font-size:9.2pt;line-height:1.28;margin:0}}
h1{{font-size:13pt;text-align:center;margin:0 0 5px}}h2{{font-size:10.5pt;margin:6px 0 3px}}
h3{{font-size:9.2pt;font-weight:700;margin:5px 0 2px}}
p{{margin:2px 0 4px}}.meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:3px 8px;border-top:1px solid;border-bottom:1px solid;padding:5px 0}}
.tag{{font-size:8pt;font-weight:bold;text-align:center;margin:3px 0 6px}}
section{{break-inside:avoid}}.line{{border-bottom:1px solid #777;margin:6px 0}}
@media screen{{body{{max-width:210mm;min-height:297mm;margin:16px auto;padding:11mm 12mm;border:1px solid #ddd}}}}
</style></head><body>
<h1>RANCANGAN PENGAJARAN HARIAN</h1><div class="tag">DRAF EDITORIAL — BELUM DILULUSKAN UNTUK PRODUKSI</div>
<div class="meta">{meta}</div>
<p><b>Subjek:</b> {esc(row['subject'])} &nbsp; <b>Tahun:</b> {esc(row['year'])} &nbsp; <b>PdP:</b> {esc(row['id'])}</p>
<p><b>Unit:</b> {esc(row['unit'])} &nbsp; <b>Tajuk:</b> {esc(row['topic'])}</p>
<p><b>SK:</b> {esc(row['sk'])} &nbsp; <b>SP:</b> {esc(', '.join(row['sp']))}</p>
<p><b>Objektif:</b> {esc(row['objective'])}</p>
<p><b>BBM:</b> {esc(row['materials'])}</p>
<p><b>Pentaksiran:</b> {esc(row['assessment'])}</p>
<section><h3>Set Induksi</h3><p>{esc(row['induction'])}</p></section>
{activities}
<section><h3>Pengukuhan / Penilaian</h3><p>{esc(row['reinforcement'])}</p></section>
<section><h3>Penutup</h3><p>{esc(row['closure'])}</p></section>
<p><b>Rujukan:</b> DSKP hlm. {esc(row['dskp_page'])}; Buku Teks hlm. {esc(row['textbook_pages'])}.</p>
<section><h3>Refleksi</h3><p>{esc(reflection) if reflection else '____ / ____ murid mencapai objektif. Tindakan susulan: __________________________'}</p></section>
</body></html>"""

def preview_all(destination):
    rows, errors = audit()
    if errors:
        raise ValueError("RPH evidence audit failed: " + "; ".join(errors))
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for row in rows:
        (destination / f"rph_t5_pk_{row['id']}_PREVIEW.html").write_text(render(row), encoding="utf-8")
    return len(rows)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m scripts.pjpk_t5_rph_preview OUTPUT_DIRECTORY")
    print("Generated editorial HTML previews:", preview_all(sys.argv[1]))
