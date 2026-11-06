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
    from web.sejarah_2027_source_hash import source_paths as identity_paths
    return identity_paths(year,pdp)

def source_fingerprint(year,pdp,*,root=ROOT):
    _validate(year,pdp)
    from web.sejarah_2027_source_hash import fingerprint
    digest=fingerprint(year,pdp,root=root)
    if not digest:
        raise SejarahNotReady("Sumber Sejarah tidak lengkap atau cap jari tidak sah")
    return digest

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
    # One lesson can only be READY if its RPH, individual Markdown and RPT
    # row agree. A valid standalone JSON flag is not a release on its own.
    if plan[pdp-1].get("Status")!="READY":
        raise SejarahNotReady("RPT PdP masih DRAF")
    md_path=base/source_paths(year,pdp)[0]
    if md_path.is_symlink() or not md_path.is_file() or md_path.stat().st_size>100_000:
        raise SejarahNotReady("RPH individu belum disediakan")
    text=md_path.read_text(encoding="utf-8")
    if not any(line.strip()=="**Status:** FINAL_READY" for line in text.splitlines()):
        raise SejarahNotReady("RPH individu belum mempunyai status READY yang disahkan")
    # Independently curated release ledger: editing a lesson's own READY flags
    # can never make it deliverable. Both per-lesson and ledger approvals are required.
    manifest_path = base/"audits/sejarah_y4_y6_release_approval_manifest_20261106.json"
    if manifest_path.is_symlink() or not manifest_path.is_file() or manifest_path.stat().st_size > 2_000_000:
        raise SejarahNotReady("Rekod kelulusan bebas tidak sah")
    ledger=json.loads(manifest_path.read_text(encoding="utf-8"))
    if (ledger.get("subject")!="Sejarah" or ledger.get("academic_year")!=2027
        or ledger.get("count")!=108 or len(ledger.get("lessons",[]))!=108):
        raise SejarahNotReady("Rekod kelulusan tidak lengkap")
    entry=ledger["lessons"][36*(year-4)+pdp-1]
    if (entry.get("id")!=row["id"] or entry.get("year")!=year or entry.get("pdp")!=pdp
        or entry.get("sk")!=r["sk"] or entry.get("sp_codes")!=r["sp_codes"]
        or entry.get("release_ready") is not True
        or entry.get("exact_textbook_exercise_page_verified") is not True
        or entry.get("teacher_individual_signoff") is not True
        or entry.get("school_profile_logo_verified") is not True
        or entry.get("telegram_web_native_parity_verified") is not True):
        raise SejarahNotReady("PdP belum mempunyai kelulusan bebas dan bukti lengkap")
    signed = r.get("release_signoff",{})
    fingerprint=source_fingerprint(year,pdp,root=base)
    if (not fingerprint or entry.get("approved_source_fingerprint")!=fingerprint
        or signed.get("approved_source_fingerprint")!=fingerprint
        or not str(entry.get("teacher_approved_by") or "").strip()
        or not str(entry.get("textbook_evidence_url") or "").strip()):
        raise SejarahNotReady("Bukti atau cap jari bahan tidak disahkan")

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
