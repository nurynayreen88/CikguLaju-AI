#!/usr/bin/env python3
"""Read-only RPT DOCX audit. Requires python-docx. Never edits source files."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from docx import Document

DATE = re.compile(r"(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](20\d{2})(?!\d)")
SP = re.compile(r"(?<!\d)([1-9]\d?\.[1-9]\d?\.[1-9]\d?)(?!\d)")
JAWI = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]")
YEAR_RANGE = re.compile(r"(\d{1,2}[./-]\d{1,2}[./-]20\d{2})\s*[–-]\s*(\d{1,2}[./-]\d{1,2}[./-]20\d{2})")

def parse_date(s):
    import datetime
    d, m, y = map(int, re.split(r"[./-]", s))
    return datetime.date(y, m, d)

def audit(path):
    source = Path(path)
    doc = Document(source)
    rows = []
    for ti, table in enumerate(doc.tables):
        for ri, row in enumerate(table.rows):
            cells = [cell.text for cell in row.cells]
            rows.append({"table": ti + 1, "row": ri + 1, "cells": len(cells),
                         "sha256": hashlib.sha256("\x1f".join(cells).encode("utf-8")).hexdigest()})
    text = "\n".join([p.text for p in doc.paragraphs] +
                     [cell.text for t in doc.tables for row in t.rows for cell in row.cells])
    anomalies = []
    for match in YEAR_RANGE.finditer(text):
        try:
            a, b = map(parse_date, match.groups())
            if b < a or (b-a).days > 14:
                anomalies.append({"range": match.group(0), "reason": "reversed_or_long_range"})
        except ValueError:
            anomalies.append({"range": match.group(0), "reason": "invalid_date"})
    return {"source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "tables": len(doc.tables), "rows": len(rows),
            "row_manifest": rows, "paragraphs": len(doc.paragraphs),
            "jawi_arabic_chars": len(JAWI.findall(text)),
            "sp_codes": dict(sorted(Counter(SP.findall(text)).items())),
            "years_in_dates": dict(sorted(Counter(x[2] for x in DATE.findall(text)).items())),
            "date_anomalies": anomalies}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = [audit(p) for p in args.files]
    payload = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

if __name__ == "__main__":
    main()
