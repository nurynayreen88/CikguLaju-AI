#!/usr/bin/env python3
"""Read-only PJPK staging inventory audit. Never promotes drafts or writes databases."""
from __future__ import annotations
import json
import re
import sys
from collections import Counter
from pathlib import Path

MANIFEST = Path("audits/pjpk_2027_staging_manifest_20261104.json")
EXPECTED = {
    "year2_pj": 41, "year2_pk": 18,
    "year3_pj": 38, "year3_pk": 9,
    "year4_pj": 34, "year4_pk": 9,
    "year5_pj": 33, "year5_pk": 12,
    "year6_pj": 34, "year6_pk": 9,
}
PATTERN = re.compile(r"^rph_standalone/pjpk/year([2-6])_(pj|pk)/[A-Za-z0-9_]+\.md$")
RELEASE_FLAGS = (
    "rpt_2027_exact_slot_verified", "textbook_page_verified",
    "pedagogical_qa_verified", "word_a4_verified",
    "telegram_runtime_verified", "web_runtime_verified", "production_ready",
)


def check(root: Path) -> dict:
    try:
        manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return {"result": "FAIL", "issues": [f"Manifest unavailable: {error}"]}
    errors, seen, counts = [], set(), Counter()
    records = manifest.get("records")
    if manifest.get("schema_version") != 1 or not isinstance(records, list):
        return {"result": "FAIL", "issues": ["Unexpected manifest schema"]}
    for item in records:
        p = item.get("path", "")
        match = PATTERN.fullmatch(p)
        if not match:
            errors.append(f"Unexpected path {p}")
            continue
        if p in seen:
            errors.append(f"Duplicate {p}")
            continue
        seen.add(p)
        yr, sub = int(match.group(1)), match.group(2)
        counts[f"year{yr}_{sub}"] += 1
        if item.get("year") != yr or item.get("component") != sub.upper():
            errors.append(f"Wrong year/subject {p}")
        if item.get("status") != "DRAFT_NOT_APPROVED":
            errors.append(f"Wrong status {p}")
        if item.get("dskp_code_presence_checked") is not True:
            errors.append(f"Missing SP code audit flag {p}")
        for key in RELEASE_FLAGS:
            if item.get(key) is not False:
                errors.append(f"Unsafe gate {key} in {p}")
        target = root / p
        if not target.is_file() or target.is_symlink():
            errors.append(f"File absent/symlink {p}")
            continue
        source = target.read_text(encoding="utf-8")
        if len(source) < 600 or not source.startswith("# RPH Pendidikan"):
            errors.append(f"Truncated header {p}")
        if "DRAF" not in source[:700]:
            errors.append(f"Not marked draft {p}")
        if not re.search(r"\*\*(?:SK|Standard Kandungan)[^*]*\*\*", source[:1300]):
            errors.append(f"Missing SK label {p}")
        if not re.search(r"\*\*(?:SP|Standard Pembelajaran)[^*]*\*\*", source[:1300]):
            errors.append(f"Missing SP label {p}")
        if "**Penutup" not in source:
            errors.append(f"Missing closure {p}")
    for key, n in EXPECTED.items():
        if counts[key] != n:
            errors.append(f"Wrong count {key}: {counts[key]} != {n}")
    if len(records) != 237 or len(seen) != 237:
        errors.append("Snapshot is not 237 unique records")
    if manifest.get("counts") != EXPECTED:
        errors.append("Manifest scope counts differ")
    actual = {str(f.relative_to(root)) for f in (root / "rph_standalone/pjpk").glob("year*_*/*.md")}
    if actual != seen:
        errors.append(f"File inventory drift: {len(actual-seen)} extra / {len(seen-actual)} missing")
    critical = root / "rph_standalone/pjpk/year6_pj/lesson_033.md"
    if critical.is_file():
        text = critical.read_text(encoding="utf-8")
        if "DRAF TERHALANG" not in text or "KONFLIK DSKP/RPT" not in text:
            errors.append("Year 6 PJ PdP 033 source conflict not blocked")
    return {"result": "FAIL" if errors else "PASS_STATIC_ONLY",
            "count": len(records), "scopes": dict(counts),
            "issues": errors,
            "note": "Static integrity is not DSKP editorial, 1-page A4 or runtime approval."}


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    result = check(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["result"] == "PASS_STATIC_ONLY" else 1)
