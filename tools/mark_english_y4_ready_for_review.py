"""Bulk-label existing Year 4 standalone RPH READY for later teacher review.

Preserve all lesson content and verification notes. This is an editorial
release status requested by the owner, NOT a claim that pending QA passed.
"""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1] / "rph_standalone/english/year4"
label = "**QA status:** READY — provisional, pending teacher's final review. Existing source/audio and Word/PDF verification notes below remain applicable."
count = 0
for n in range(1, 161):
    p = root / f"lesson_{n:03d}.md"
    if not p.is_file():
        raise SystemExit(f"Missing RPH: {p}")
    s = p.read_text(encoding="utf-8")
    if "READY — provisional, pending teacher's final review" in s:
        continue
    # Replace old editorial status lines, never alter teaching activities or source references.
    s = re.sub(r"(?mi)^\*\*(?:QA status|Status):\*\*[^\n]*\n?", "", s)
    s = s.rstrip() + "\n\n" + label + "\n"
    p.write_text(s, encoding="utf-8")
    count += 1
print(f"Updated {count} of 160 RPH; lesson content preserved.")
