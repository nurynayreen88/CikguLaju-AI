"""Build the verified, teacher-facing Islamic Education Y4 RPT static PDF.

Run in a disposable staging checkout. Original binary remains retrievable by
prior Git commit; do not alter database, Telegram, or production services.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

import fitz

from web.rpt_private_notes import _strip, _NOTES, _page_chars


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "rpt_2027" / "web_2027_pdfs"
PDF = ASSETS / "pendidikan_islam" / "tahun_4.pdf"
MANIFEST = ASSETS / "manifest.json"
COVER = ASSETS / "original_cover_layout_verified.json"
AUDIT = ASSETS / "PI4_INTERNAL_PROSE_20261108_DRAF_AUDIT.json"
KEY = "pendidikan_islam:4"
EXPECTED = {"mapping": 16, "developer_note": 38}


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def inspect_pdf(binary):
    with fitz.open(stream=binary, filetype="pdf") as pdf:
        content = "\n".join(page.get_text("text") for page in pdf)
        markers = Counter()
        for page in pdf:
            text, _ = _page_chars(page)
            for i, expression in enumerate(_NOTES):
                markers["mapping" if i == 0 else "developer_note"] += len(
                    expression.findall(text)
                )
        ids = re.findall(r"PdP\s+(\d{3})", content)
        return {
            "pages": len(pdf),
            "unique_pdp": len(set(ids)),
            "pdp": ids,
            "markers": dict(markers),
            "all_pages_draft": all(
                "DRAF SEMAKAN" in page.get_text()
                for page in list(pdf)[1:]
            ),
            "links": sum(len(page.get_links()) for page in pdf),
            "text": content,
        }


def main():
    manifest = json.loads(MANIFEST.read_text("utf-8"))
    layout = json.loads(COVER.read_text("utf-8"))
    assert manifest["status"] == "DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
    assert manifest["count"] == 56 and len(manifest["files"]) == 56
    assert layout["status"] == "ORIGINAL_COVER_TEMPLATE_LOCKED_TO_56_SOURCE_PDF_SHA256"
    assert set(layout["source_sha256_by_subject_year"]) == set(manifest["files"])
    entry = manifest["files"][KEY]
    raw = PDF.read_bytes()
    old_hash = sha256(raw).hexdigest()
    assert old_hash == entry["sha256"]
    assert old_hash == layout["source_sha256_by_subject_year"][KEY]
    assert len(raw) == entry["bytes"]
    before = inspect_pdf(raw)
    assert before["pages"] == entry["pages"] == 76
    assert before["unique_pdp"] == 151
    assert before["all_pages_draft"]

    fixed = _strip(raw)
    if fixed is None:
        # Re-running the workflow must not rewrite history or mark DRAF READY.
        audit = json.loads(AUDIT.read_text("utf-8"))
        assert audit["clean_sha256"] == old_hash
        assert not any(before["markers"].values())
        print("PI4_INTERNAL_NOTES_ALREADY_REMOVED_AND_VERIFIED")
        return

    assert before["markers"] == EXPECTED, before["markers"]
    after = inspect_pdf(fixed)
    assert after["pages"] == before["pages"]
    assert after["unique_pdp"] == 151
    assert after["pdp"] == before["pdp"]
    assert after["all_pages_draft"]
    assert after["links"] == before["links"]
    assert not any(after["markers"].values())
    assert "Pemetaan buku teks belum" not in after["text"]
    assert "tidak mereka halaman buku teks" not in after["text"]

    with (fitz.open(stream=raw, filetype="pdf") as original,
          fitz.open(stream=fixed, filetype="pdf") as clean):
        assert original[0].get_pixmap(alpha=False).samples == clean[0].get_pixmap(alpha=False).samples
        for i in range(1, len(original)):
            # Only the Catatan/Bahan column (x < 200 pt) may change.
            right_clip = fitz.Rect(200, 0, original[i].rect.width, original[i].rect.height)
            a = original[i].get_pixmap(clip=right_clip, alpha=False)
            b = clean[i].get_pixmap(clip=right_clip, alpha=False)
            assert a.samples == b.samples, f"Unexpected layout change page {i+1}"

    new_hash = sha256(fixed).hexdigest()
    if new_hash == old_hash:
        raise AssertionError("Expected source cleanup to change the binary")
    # Only the exact Y4 source entry and corresponding cover-provenance hash
    # change; 55 other original RPT assets remain untouched.
    manifest["files"][KEY]["sha256"] = new_hash
    manifest["files"][KEY]["bytes"] = len(fixed)
    layout["source_sha256_by_subject_year"][KEY] = new_hash

    PDF.write_bytes(fixed)
    write_json(MANIFEST, manifest)
    write_json(COVER, layout)
    write_json(AUDIT, {
        "status": "DRAF_INTERNAL_PROSE_REMOVED_NOT_ACADEMIC_READY",
        "subject": "pendidikan_islam",
        "year": 2027,
        "class_year": 4,
        "original_sha256": old_hash,
        "clean_sha256": new_hash,
        "source_pdf": "pendidikan_islam/tahun_4.pdf",
        "source_size_bytes": len(raw),
        "clean_size_bytes": len(fixed),
        "pages": 76,
        "unique_pdp": 151,
        "removed": before["markers"],
        "other_55_rpt_sources_unchanged": True,
        "cover_identical": True,
        "all_sp_and_jawi_preserved": True,
        "mapping_academic_final_approved": False,
        "notes": "Developer-only prose removed; teacher-facing RPT remains DRAF."
    })
    print("PI4_INTERNAL_NOTES_CLEANED", json.dumps({
        "before": old_hash,
        "after": new_hash,
        "removed": before["markers"],
        "other_rpt_files_changed": 0,
    }))


if __name__ == "__main__":
    main()
