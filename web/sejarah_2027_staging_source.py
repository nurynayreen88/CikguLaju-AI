"""Fail-closed immutable Sejarah 2027 source for an eventual shared Telegram/Web adapter.

An offline QA preview may read drafts; public delivery is prohibited until a
human verifies book exercise pages, pedagogy, and native RPH/PDF parity.
No Flask, Telegram, payment, database or deployment side effects.
"""
from __future__ import annotations

from hashlib import sha256
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class SejarahNotReady(PermissionError):
    pass

def _validate(year,pdp):
    if type(year) is not int or year not in (4,5,6):
        raise ValueError("Sejarah supported Years 4–6 only")
    if type(pdp) is not int or not 1<=pdp<=36:
        raise ValueError("Sejarah PdP must be 1..36")

def source_paths(year,pdp):
    _validate(year,pdp)
    return (
        "rph_standalone/sejarah/tahun_%d/RPH_SEJ-T%d-PDP-%03d.md" % (year,year,pdp),
        "rph_standalone/sejarah/y%d_2027_rph_DRAF.json" % year,
        "curriculum/sejarah/y%d_dskp_crosswalk_DRAF.json" % year,
        "curriculum/sejarah/y%d_buku_teks_unit_map_20261106.json" % year,
        "curriculum/sejarah/kalender_sejarah_2027_kumpulan_a_b.json",
        "rpt_2027/sejarah/RPT_SEJARAH_TAHUN_%d_2027_A_B_DRAF.csv" % year,
    )

def source_fingerprint(year,pdp,*,root=ROOT):
    base=Path(root).resolve()
    digest=sha256()
    for rel in source_paths(year,pdp):
        path=base/rel
        if path.is_symlink() or not path.is_file() or path.stat().st_size>4_000_000:
            raise SejarahNotReady("Sumber Sejarah tidak lengkap")
        raw=path.read_bytes()
        if not raw:
            raise SejarahNotReady("Sumber Sejarah kosong")
        digest.update(rel.encode("utf-8")+b"\x00"+raw+b"\x00")
    return digest.hexdigest()

def lesson(year,pdp,*,root=ROOT):
    """Return a copied source row for QA only, never a live RPH export."""
    _validate(year,pdp)
    base=Path(root).resolve()
    path=base/f"rph_standalone/sejarah/y{year}_2027_rph_DRAF.json"
    if path.is_symlink() or not path.is_file() or path.stat().st_size>4_000_000:
        raise SejarahNotReady("RPH Sejarah tidak tersedia")
    obj=json.loads(path.read_text(encoding="utf-8"))
    items=obj.get("lessons",[])
    if len(items)!=36: raise SejarahNotReady("Bilangan PdP tidak lengkap")
    row=items[pdp-1]
    r=row["rph"]
    if row["id"]!=f"SEJ-T{year}-PDP-{pdp:03d}" or row["num"]!=pdp:
        raise SejarahNotReady("Identiti PdP tidak padan")
    if r["year"]!=year or r["academic_year"]!=2027 or r["subject"]!="Sejarah":
        raise SejarahNotReady("Kurikulum atau tahun bercanggah")
    standards=json.loads((base/f"curriculum/sejarah/y{year}_dskp_crosswalk_DRAF.json").read_text(encoding="utf-8"))
    valid={x["code"] for sk in standards["standards"] for x in sk["sp"]}
    if not set(r["sp_codes"])<=valid or not r["sp_codes"]:
        raise SejarahNotReady("Kod SP tidak sah")
    with (base/f"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{year}_2027_A_B_DRAF.csv").open(newline="",encoding="utf-8") as fh:
        plan=list(csv.DictReader(fh))
    if len(plan)!=36 or plan[pdp-1]["ID"]!=row["id"]:
        raise SejarahNotReady("RPT dan RPH tidak sepadan")
    # Missing approval evidence always fails closed, even when status is forged.
    checks=(
        r.get("teacher_approval") is True,
        r.get("textbook_page_verified") is True,
        r.get("textbook_reference",{}).get("exact_activity_page_confirmed") is True,
        isinstance(r.get("release_signoff",{}).get("approved_by"),str) and bool(r["release_signoff"]["approved_by"].strip()),
        r.get("release_signoff",{}).get("web_telegram_parity_verified") is True,
        r.get("release_signoff",{}).get("word_pdf_layout_verified") is True,
        r.get("status")=="FINAL_READY",
    )
    if not all(checks):
        raise SejarahNotReady("Sejarah Tahun 4–6 belum FINAL READY; eksport pengguna ditutup")
    # This release function intentionally does not generate/send the document.
    # It only returns an approved immutable source row for the native renderer.
    return json.loads(json.dumps(row,ensure_ascii=False))

def preview_only(year,pdp,*,root=ROOT):
    """Explicit internal review path: cannot be called as a public exporter."""
    _validate(year,pdp)
    base=Path(root).resolve()
    obj=json.loads((base/f"rph_standalone/sejarah/y{year}_2027_rph_DRAF.json").read_text(encoding="utf-8"))
    return json.loads(json.dumps(obj["lessons"][pdp-1],ensure_ascii=False))
