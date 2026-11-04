#!/usr/bin/env python3
"""Audit fail-closed untuk BM Tahun 3 2027. Tiada akses produksi."""
from collections import Counter
from html import unescape
from pathlib import Path
import json
import re
import sys

BASE = Path(__file__).resolve().parents[1]
RPT_BASE = BASE / "rpt_2027" / "bahasa_melayu"
MD = RPT_BASE / "keluaran_format_english" / "RPT_BM_TAHUN_3_2027_A_B_PER_LESSON_DRAF.md"
HTML = MD.with_suffix(".html")
RPH = BASE / "rph_standalone" / "bahasa_melayu" / "year3"
GATE = RPT_BASE / "READY_GATE.json"
EXPECTED = set(range(1, 166))
EXPECTED_PKJR = {3, 9, 10, 19, 30, 35, 40, 44, 50, 58, 66, 75, 79, 84, 89,
                 94, 96, 101, 107, 112, 116, 120, 125, 139, 145, 151, 157, 162}
EXPECTED_HOLD = set()

def norm(s):
    s = re.sub(r"<[^>]*>", "", s)
    return " ".join(unescape(s).split())

def field(source, key_regex):
    m = re.search(r"^\*\*(?:" + key_regex + r"):\*\*\s*(.*)$", source, re.M)
    return norm(m.group(1)) if m else ""

def audit():
    errors = []
    markdown_rows = {}
    for line in MD.read_text(encoding="utf-8").splitlines():
        mat = re.search(r"\*\*PdP (\d{3})\*\* \(BM3-P(\d{3})\)", line)
        if not mat:
            continue
        n, idn = int(mat.group(1)), int(mat.group(2))
        parts = [norm(x) for x in line.strip().strip("|").split("|")]
        if len(parts) != 7 or n != idn or n in markdown_rows:
            errors.append(f"RPT MD baris tidak sah atau berganda: PdP {n}")
            continue
        markdown_rows[n] = parts
    if set(markdown_rows) != EXPECTED:
        errors.append("RPT Markdown: 165 ID unik tidak lengkap")

    raw_html = HTML.read_text(encoding="utf-8")
    html_rows = {}
    for mat in re.finditer(r'<tr><td class="id">PdP (\d{3})<div class="sub">BM3-P(\d{3})</div></td>(.*?)</tr>',
                           raw_html, re.S):
        n, idn = int(mat.group(1)), int(mat.group(2))
        values = [norm(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", mat.group(3), re.S)]
        if n != idn or len(values) != 6 or n in html_rows:
            errors.append(f"RPT HTML baris tidak sah/berganda: {n}")
            continue
        html_rows[n] = values
    if set(html_rows) != EXPECTED:
        errors.append("RPT HTML: 165 ID unik tidak lengkap")
    for n in EXPECTED & markdown_rows.keys() & html_rows.keys():
        if markdown_rows[n][1:] != html_rows[n]:
            errors.append(f"RPT Markdown/HTML tidak sepadan PdP {n:03d}")

    files = {int(p.stem.split("_")[-1]):p for p in RPH.glob("lesson_*.md")
             if re.fullmatch(r"lesson_\d{3}", p.stem)}
    if set(files) != EXPECTED:
        errors.append("RPH: fail 001–165 tidak lengkap")
    statuses = Counter()
    holds = set()
    pkjr = set()
    for n in sorted(EXPECTED & files.keys() & markdown_rows.keys()):
        content = files[n].read_text(encoding="utf-8")
        row = markdown_rows[n]
        sk = field(content, r"SK|Standard Kandungan \(SK\)")
        sp = field(content, r"SP|Standard Pembelajaran \(SP\)")
        status = field(content, "Status QA").split(" ")[0].strip()
        if sk != row[3]:
            errors.append(f"SK tidak padan: {n:03d}")
        if sp != row[4]:
            errors.append(f"SP tidak padan: {n:03d}")
        if status not in ("DRAF", "HOLD", "READY"):
            errors.append(f"Status QA tidak sah: {n:03d}")
        else:
            statuses[status] += 1
            if status == "HOLD":
                holds.add(n)
        if not all(x in content.lower() for x in ("set induksi", "aktiviti 1", "aktiviti 2", "penutup")):
            errors.append(f"Langkah utama RPH tiada: {n:03d}")
        if not any(x in content.lower() for x in ("pbd", "pentaksiran", "penilaian")):
            errors.append(f"Pentaksiran RPH tiada: {n:03d}")
        if re.search(r"\+\s*pkjr", row[2], re.I):
            pkjr.add(n)
            if "## Integrasi PKJR" not in content:
                errors.append(f"Aktiviti PKJR tiada: {n:03d}")
    if pkjr != EXPECTED_PKJR:
        errors.append(f"Penanda PKJR bukan 28 ID yang dijangka: {sorted(pkjr ^ EXPECTED_PKJR)}")
    if holds != EXPECTED_HOLD:
        errors.append(f"Senarai HOLD tidak sepadan dengan audit: {sorted(holds ^ EXPECTED_HOLD)}")
    if statuses.get("READY", 0):
        errors.append("READY telah ditandakan sebelum QA akademik/produksi diluluskan")
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    yg = gate["year_gates"]["3"]
    if gate["status"] != "DRAFT_NOT_PUBLISHED" or gate["verified_strict_ready"]:
        errors.append("Gate tidak fail-closed")
    if yg.get("rph_all_present") is not True:
        errors.append("Gate rph_all_present Tahun 3 salah")
    for key, value in yg.items():
        if key != "rph_all_present" and value is not False:
            errors.append(f"Gate belum disahkan telah dibuka: {key}")
    print(json.dumps({
        "RPT_MD":len(markdown_rows),
        "RPT_HTML":len(html_rows),
        "RPH":len(files),
        "PKJR":len(pkjr),
        "statuses":dict(statuses),
        "hold_lessons":sorted(holds),
        "READY_gate":gate["status"],
        "errors":len(errors)
    }, ensure_ascii=False, indent=2))
    for issue in errors[:80]:
        print("ERROR:", issue)
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(audit())
