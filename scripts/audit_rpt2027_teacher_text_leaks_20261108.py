"""Detect internal developer/reviewer notes leaked into RPT 2027 teacher output.

Read-only by design: this audit never edits a PDF, source CSV, RPH or DB.
A clean result covers text that the extractor can read; it is not an
academic SK/SP or curriculum sign-off.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

RULES = {
    "READY_INTERNAL": r"\b(?:PRA[\s-]?READY|PRE[\s-]?READY|SEBELUM\s+READY|NOT\s+READY)\b",
    "TEXTBOOK_MAPPING_REVIEW": r"pemetaan\s+buku\s+teks\s+belum\s+disah(?:kan)?",
    "DEVELOPER_INSTRUCTION": r"rujuk\s+buku\s+dan\s+DSKP\s+sebelum\s+READY",
    "UNVERIFIED_REFERENCE": r"(?:buku\s+aktiviti|BA|halaman\s+(?:BT|buku\s+teks)|rujukan\s+buku\s+teks)\s+(?:belum\s+disah(?:kan)?|belum\s+sah)",
    "INTERNAL_CHECKPOINT": r"(?:DRAF\s+(?:TERKAWAL|SEMAK(?:AN)?|UNTUK\s+SEMAKAN)|STATUS\s+DRAF)",
    "EDITOR_ACTION": r"(?:semak\s+tajuk\s+penuh|pengesahan\s+instrumen\s+belum\s+selesai|pengesahan\s+guru\s+belum\s+(?:dibuat|selesai)|kelulusan\s+guru\s+masih\s+tertangguh)",
    "UNVERIFIED_CANDIDATE": r"(?:calon\s+teks\s+digital|belum\s+dipadankan|tiada\s+janaan\s+automatik\s+sehingga\s+pengesahan\s+selesai)",
    "RELEASE_COMMAND": r"(?:JANGAN\s+MERGE|JANGAN\s+DEPLOY|RELEASE\s+BLOCKED|BUKAN\s+UNTUK\s+GURU)",
    "INTERNAL_SOURCE_ID": r"\b(?:Sumber|Source)\s*:\s*[A-Za-z0-9_]{4,}",
    "UNHELPFUL_REFERENCE_DIRECTIVE": r"\bRujukan\s*:\s*Rujuk\s+DSKP\b",
    "HELD_REVIEW_ONLY": r"\bHOLD\s*:",
    "HELD_BM_SP_CROSSWALK": r"\bHOLD\s+(?:padanan|tajuk|SP|rujukan|kod)\b",
    "SOURCE_SOW_PROVENANCE": r"\bMain/Complementary\s+codes\s+from\s+source\s+SOW\b",
    "NO_INVENTED_TEXTBOOK_PAGE": r"tidak\s+mereka\s+halaman\s+buku\s+teks",
    "INTERNAL_SAINS_ID": r"\bSCI-Y[2-6]-PDP-\d{3}\b",
    "INTERNAL_BM_ID": r"\bBM[2-6]-P\d{3}\b",
    "BM_EDITORIAL_INSTRUCTION": r"(?:Semak\s+judul\s+aktiviti\s+penuh|BA\s+asal\s+belum\s+disemak|jangan\s+dakwa\s+kedua-duanya\s+setara)",
    "INTERNAL_TASMI_STANDARD_FLAG": r"(?:TIADA\s+KOD\s+SP\s+RASMI\s+DALAM\s+RPT\s+SUMBER|BUKAN\s+KOD\s+SK\s+RASMI)",
    "RPT_SOURCE_PHRASE": r"\bRPT\s+sumber\b",
    # Music source provenance is kept in internal CSV/ledger, never printed
    # in the RPT teacher PDF. This is distinct from legitimate SK/SP words
    # such as "menulis draf dan menghasilkan penulisan".
    "MUSIC_DRAFT_BOOK_PAGE": r"\(\s*draf\s*\)",
    "MUSIC_MISSING_NOTATION": r"\bSimbol\s*/\s*skor\s+tidak\s+penuh\s+dalam\s+teks\b",
    "MUSIC_EDITOR_STATUS": r"\bPengukuhan\s+pilihan,\s*bukan\s+projek\s+rasmi\s*;\s*DRAF\b",
    "EMPTY_BOOK_PAGE": r"\bBT\s+m/s\s*:\s*(?:[.|]|\Z)",
}
_COMPILED = tuple((key, re.compile(value, flags=re.IGNORECASE)) for key, value in RULES.items())
SUFFIXES = frozenset((".pdf", ".html", ".htm", ".csv", ".txt"))


def find_internal_notes(text: str) -> list[dict]:
    """Return evidence, not a rewritten/automatically approved curriculum."""
    if not isinstance(text, str):
        raise TypeError("Text must be a string")
    flattened = re.sub(r"\s+", " ", text)
    findings = []
    for code, regex in _COMPILED:
        for match in regex.finditer(flattened):
            findings.append({
                "rule": code,
                "match": match.group(0),
                "context": flattened[max(0, match.start()-65):match.end()+65].strip()
            })
    return sorted(findings, key=lambda entry: (entry["context"], entry["rule"]))


def _parts(path: Path):
    if path.suffix.lower() == ".pdf":
        try:
            import fitz
        except ImportError:
            # Keep the audit usable locally when only pypdf is installed.
            from pypdf import PdfReader
            document = PdfReader(str(path))
            for page_number, page in enumerate(document.pages, 1):
                yield page_number, page.extract_text() or ""
        else:
            # GitHub's five PDF QA jobs already depend on PyMuPDF.
            with fitz.open(path) as document:
                for page_number, page in enumerate(document, 1):
                    yield page_number, page.get_text("text") or ""
    else:
        source = path.read_text(encoding="utf-8-sig")
        if path.suffix.lower() in (".html", ".htm"):
            source = html.unescape(re.sub(r"<[^>]+>", " ", source))
        yield 1, source


def scan_file(path: Path) -> list[dict]:
    """Scan every extractable PDF page or text file, retaining exact file/page."""
    findings = []
    is_pdf = path.suffix.lower() == ".pdf"
    has_extractable_text = False
    unreadable_body_pages = []
    for page_number, text in _parts(path):
        # RPT preview pages after the cover contain five-column teaching
        # tables. A single image-only body page must never be called clean
        # just because another page (or the cover) has searchable text.
        readable = bool(re.search(r"\w", text))
        if is_pdf:
            has_extractable_text |= readable
            if page_number > 1 and not readable:
                unreadable_body_pages.append(page_number)
        for item in find_internal_notes(text):
            findings.append({"file": str(path), "page": page_number, **item})
    if is_pdf and not has_extractable_text:
        raise ValueError("PDF has no extractable text; manual visual review required")
    if unreadable_body_pages:
        raise ValueError(
            "PDF body pages have no extractable text: "
            + ", ".join(map(str, unreadable_body_pages))
            + "; manual visual review required"
        )
    return findings


def scan_paths(paths, teacher_output_only=False, pdf_only=False) -> dict:
    files = set()
    suffixes = ({".pdf"} if pdf_only else
                {".pdf", ".html", ".htm"} if teacher_output_only else SUFFIXES)
    for path in map(Path, paths):
        if path.is_file() and path.suffix.lower() in suffixes:
            files.add(path)
        elif path.is_dir():
            files.update(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in suffixes)
    all_findings = []
    errors = []
    for path in sorted(files):
        try:
            all_findings.extend(scan_file(path))
        except Exception as exc:
            errors.append({"file": str(path), "error": type(exc).__name__ + ": " + str(exc)})
    return {"scanned_files": len(files), "findings_count": len(all_findings),
            "files_with_findings": len({f["file"] for f in all_findings}),
            "findings": all_findings, "read_errors": errors,
            "academic_signoff": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="RPT files and/or directories")
    parser.add_argument("--teacher-output-only", action="store_true",
                        help="Scan rendered HTML/PDF, not source CSV")
    parser.add_argument("--pdf-only", action="store_true",
                        help="Audit only PDF files, excluding HTML source templates")
    parser.add_argument("--fail-on-findings", action="store_true",
                        help="Fail release gate on leaked notes or unreadable files")
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args(argv)
    report = scan_paths(args.paths, args.teacher_output_only, args.pdf_only)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "findings"},
                     ensure_ascii=False, indent=2))
    for finding in report["findings"][:30]:
        print(f'{finding["file"]} p.{finding["page"]}: '
              f'{finding["rule"]}: {finding["match"]}')
    # Unreadable PDFs must NEVER produce an apparent clean audit, even for
    # report-only staging runs. Flagged draft phrases remain informational
    # unless an explicitly requested release gate is active.
    return int(bool(report["read_errors"] or not report["scanned_files"] or
                    (args.fail_on_findings and report["findings_count"])))


if __name__ == "__main__":
    raise SystemExit(main())
