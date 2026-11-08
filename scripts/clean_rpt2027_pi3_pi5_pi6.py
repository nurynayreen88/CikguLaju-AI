"""Stage clean static Pendidikan Islam Tahun 3, 5 and 6 RPT2027 PDFs.

Only redact explicit, exact developer-note variants. Preserve academic DRAF
status, Jawi, SK/SP, original cover, unchanged 53 other PDF assets and history.
"""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import re

import fitz

from web.rpt_private_notes import _strip, _NOTES, _page_chars

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rpt_2027" / "web_2027_pdfs"
MANIFEST = BASE / "manifest.json"
COVER = BASE / "original_cover_layout_verified.json"
AUDIT = BASE / "PI356_INTERNAL_PROSE_20261108_DRAF_AUDIT.json"
YEARS = {
    3: {"pages": 75, "pdp": 147, "mapping": 16, "developer": 0},
    5: {"pages": 72, "pdp": 143, "mapping": 17, "developer": 36},
    6: {"pages": 73, "pdp": 143, "mapping": 0, "developer": 32},
}


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def inspect(binary):
    with fitz.open(stream=binary, filetype="pdf") as pdf:
        snippets = []
        counts = Counter()
        for pg in pdf:
            text, _ = _page_chars(pg)
            snippets.append(pg.get_text("text"))
            for i, pattern in enumerate(_NOTES):
                counts["developer" if i == 1 else "mapping"] += len(pattern.findall(text))
        full = "\n".join(snippets)
        ids = re.findall(r"PdP\s+(\d{3})", full)
        return {
            "pages": len(pdf),
            "unique_pdp": len(set(ids)),
            "all_pdp": ids,
            "draft": all("DRAF SEMAKAN" in pg.get_text() for pg in list(pdf)[1:]),
            "links": sum(len(pg.get_links()) for pg in pdf),
            "count": dict(counts),
            "full": full,
        }


def verify_change(before_data, after_data, expected):
    old, new = inspect(before_data), inspect(after_data)
    assert old["pages"] == new["pages"] == expected["pages"]
    assert old["unique_pdp"] == new["unique_pdp"] == expected["pdp"]
    assert old["all_pdp"] == new["all_pdp"]
    assert old["draft"] and new["draft"]
    assert old["links"] == new["links"]
    assert old["count"] == {"mapping": expected["mapping"], "developer": expected["developer"]}, old["count"]
    assert sum(new["count"].values()) == 0
    assert "sebelum READY" not in new["full"]
    assert "tidak mereka halaman buku teks" not in new["full"]
    with (fitz.open(stream=before_data, filetype="pdf") as orig,
          fitz.open(stream=after_data, filetype="pdf") as clean):
        assert orig[0].get_pixmap(alpha=False).samples == clean[0].get_pixmap(alpha=False).samples
        for i in range(1, len(orig)):
            # Existing five-column format: untouched SK/SP, lesson, calendar.
            right = fitz.Rect(200, 0, orig[i].rect.width, orig[i].rect.height)
            assert orig[i].get_pixmap(clip=right, alpha=False).samples == clean[i].get_pixmap(clip=right, alpha=False).samples, i
    return old


def main():
    manifest = json.loads(MANIFEST.read_text("utf-8"))
    layout = json.loads(COVER.read_text("utf-8"))
    assert manifest["count"] == len(manifest["files"]) == 56
    assert manifest["status"] == "DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
    assert layout["status"] == "ORIGINAL_COVER_TEMPLATE_LOCKED_TO_56_SOURCE_PDF_SHA256"
    assert set(layout["source_sha256_by_subject_year"]) == set(manifest["files"])
    earlier = json.loads(AUDIT.read_text("utf-8")) if AUDIT.exists() else {}
    entries = dict(earlier.get("entries", {}))
    modified = []
    for year, expected in YEARS.items():
        key = f"pendidikan_islam:{year}"
        entry = manifest["files"][key]
        path = BASE / entry["path"]
        raw = path.read_bytes()
        before_sha = sha256(raw).hexdigest()
        assert before_sha == entry["sha256"] == layout["source_sha256_by_subject_year"][key]
        assert len(raw) == entry["bytes"] and entry["pages"] == expected["pages"]
        assert entry["status"] == "DRAF"
        clean = _strip(raw)
        if clean is None:
            assert key in entries and entries[key]["clean_sha256"] == before_sha
            print("PI_ALREADY_CLEAN", key, before_sha)
            continue
        data = verify_change(raw, clean, expected)
        new_sha = sha256(clean).hexdigest()
        assert before_sha != new_sha
        path.write_bytes(clean)
        manifest["files"][key]["sha256"] = new_sha
        manifest["files"][key]["bytes"] = len(clean)
        layout["source_sha256_by_subject_year"][key] = new_sha
        entries[key] = {
            "source_sha256": before_sha,
            "clean_sha256": new_sha,
            "old_bytes": len(raw),
            "clean_bytes": len(clean),
            "pages": data["pages"],
            "unique_pdp": data["unique_pdp"],
            "notes_removed": data["count"],
            "cover_identical": True,
            "non_note_glyphs_preserved": True,
            "other_subjects_unchanged": True,
            "academic_final_approved": False,
        }
        modified.append(key)

    if modified:
        write_json(MANIFEST, manifest)
        write_json(COVER, layout)
        write_json(AUDIT, {
            "status": "DRAF_INTERNAL_PROSE_REMOVED_NOT_ACADEMIC_READY",
            "year": 2027,
            "subject": "pendidikan_islam",
            "years": [3, 5, 6],
            "unchanged_other_rpt_pdfs": 53,
            "production_telegram_database_modified": False,
            "entries": entries,
        })
    print("PI_3_5_6_STATIC_CLEAN_COMPLETE", json.dumps({
        "changed": modified, "entries": entries,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
