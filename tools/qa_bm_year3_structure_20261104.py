#!/usr/bin/env python3
"""Audit struktur RPT/RPH BM Tahun 3. Tidak menulis ke DB/produksi."""
from pathlib import Path
import re
import sys
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
RPT = ROOT / "rpt_2027/bahasa_melayu/keluaran_format_english/RPT_BM_TAHUN_3_2027_A_B_PER_LESSON_DRAF.md"
HTML = ROOT / "rpt_2027/bahasa_melayu/keluaran_format_english/RPT_BM_TAHUN_3_2027_A_B_PER_LESSON_DRAF.html"
RPH = ROOT / "rph_standalone/bahasa_melayu/year3"
def norm(s):
    return " ".join(s.split())
def extract(content, pat):
    m = re.search(pat, content, re.M)
    return norm(m.group(1)) if m else None

def main():
    errors = []
    rows = {}
    for line in RPT.read_text(encoding="utf-8").splitlines():
        match = re.search(r"\*\*PdP (\d{3})\*\* \(BM3-P(\d{3})\)", line)
        if not match:
            continue
        n = int(match.group(1))
        if match.group(1) != match.group(2) or n in rows:
            errors.append(f"Duplicate/mismatch RPT PdP {n}")
        fields = [norm(part) for part in line.strip().strip("|").split("|")]
        if len(fields) != 7:
            errors.append(f"RPT PdP {n} has {len(fields)} fields, expected 7")
            continue
        rows[n] = fields
    html = HTML.read_text(encoding="utf-8")
    html_ids = [int(n) for n in re.findall(r'<div class="sub">BM3-P(\d{3})</div>', html)]
    if len(html_ids) != 165 or sorted(html_ids) != list(range(1,166)):
        errors.append("RPT HTML missing/duplicate IDs")
    if sorted(rows) != list(range(1,166)):
        errors.append("RPT Markdown missing/duplicate IDs")
    files = sorted(RPH.glob("lesson_*.md"))
    present = [int(f.stem.split("_")[1]) for f in files if re.fullmatch(r"lesson_\d{3}",f.stem)]
    if len(present) != 165 or sorted(present) != list(range(1,166)):
        errors.append("RPH file sequence incomplete/duplicated")
    statuses = Counter()
    for n in range(1,166):
        path = RPH / f"lesson_{n:03d}.md"
        if not path.is_file() or n not in rows:
            continue
        content = path.read_text(encoding="utf-8")
        sk = extract(content, r"^\*\*(?:SK|Standard Kandungan \(SK\)):\*\*\s*(.+)$")
        sp = extract(content, r"^\*\*(?:SP|Standard Pembelajaran \(SP\)):\*\*\s*(.+)$")
        status = extract(content, r"^\*\*Status QA:\*\*\s*(DRAF|HOLD|READY)")
        if sk != rows[n][3]:
            errors.append(f"SK mismatch {n:03d}: {sk!r}")
        if sp != rows[n][4]:
            errors.append(f"SP mismatch {n:03d}: {sp!r}")
        if not status:
            errors.append(f"Missing status {n:03d}")
        else:
            statuses[status] += 1
        if not all(k.lower() in content.lower() for k in ["Set induksi", "Aktiviti 1", "Aktiviti 2", "Penutup"]):
            errors.append(f"Missing core RPH phase {n:03d}")
    print("RPT: ",len(rows),"RPH: ",len(present),"Status:",dict(statuses))
    print("Errors:",len(errors))
    for e in errors[:50]:
        print(" -",e)
    if statuses.get("READY",0):
        print("WARN: READY must be academically approved, not inferred from this structural QA.")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
