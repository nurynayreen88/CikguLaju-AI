"""Read-only contamination audit of all 56 static RPT2027 teacher PDFs."""
from collections import Counter
from pathlib import Path
import json
import re

import fitz

from web.rpt_private_notes import _NOTES, _page_chars

ASSETS = Path(__file__).resolve().parents[1] / "rpt_2027" / "web_2027_pdfs"
PROBES = {
    "unverified_mapping": re.compile(r"pemetaan\s+buku\s+teks\s+belum", re.I),
    "before_ready": re.compile(r"sebelum\s+READY", re.I),
    "developer_fabrication": re.compile(r"tidak\s+mereka", re.I),
    "development_label": re.compile(r"catatan\s+(?:dalaman|pembangun)", re.I),
    "unverified_source": re.compile(r"(?:belum|tidak)\s+disahkan", re.I),
}


def main():
    manifest = json.loads((ASSETS / "manifest.json").read_text("utf-8"))
    entries = manifest["files"]
    assert len(entries) == 56 and manifest["status"] == "DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
    found = {}
    totals = Counter()
    for key, entry in sorted(entries.items()):
        path = ASSETS / entry["path"]
        assert path.is_file(), key
        counts = Counter()
        where = {}
        with fitz.open(path) as pdf:
            assert len(pdf) == entry["pages"]
            for no, page in enumerate(pdf, 1):
                text, _ = _page_chars(page)
                matched = False
                for i, expr in enumerate(_NOTES):
                    amount = len(expr.findall(text))
                    if amount:
                        counts["remove_mapping" if i == 0 else "remove_developer_note"] += amount
                        matched = True
                for label, expr in PROBES.items():
                    amount = len(expr.findall(text))
                    if amount:
                        counts[label] += amount
                        matched = True
                if matched:
                    where[str(no)] = {
                        label: len(expr.findall(text))
                        for label, expr in PROBES.items()
                        if expr.search(text)
                    }
        if counts:
            found[key] = {
                "counts": dict(counts),
                "pages_with_markers": list(where),
            }
            totals.update(counts)
    print("RPT2027_56_PDF_INTERNAL_NOTE_AUDIT=" + json.dumps({
        "total_source_pdfs": len(entries),
        "affected_pdfs": len(found),
        "counts": dict(totals),
        "affected": found,
    }, ensure_ascii=False, sort_keys=True))
    if totals["unverified_mapping"] != totals["remove_mapping"]:
        print("WARNING_OTHER_PEMETAAN_VARIANTS_DETECTED")
    if totals["developer_fabrication"] != totals["remove_developer_note"]:
        print("WARNING_OTHER_DEVELOPER_NOTE_VARIANTS_DETECTED")


if __name__ == "__main__":
    main()
