"""Validate 48 v76 Word files against their filename, state and year.

Usage: python scripts/verify_rpt_pj_2027_v76.py ARCHIVE.zip
Read-only; no changes to archive or application data.
"""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree as ET
import sys
import re

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rpt_pj_2027_delivery import FILE_PATTERN, STATES, YEARS

def verify(archive):
    expected = {
        "RPT_PJ_2027_DOCX/" + FILE_PATTERN.format(state=state, year=year): (state, year)
        for state in STATES for year in YEARS
    }
    problems = []
    try:
        bundle = ZipFile(archive)
    except (BadZipFile, OSError, ValueError) as exc:
        return ["Invalid RPT archive: " + str(exc)]
    with bundle:
        members = bundle.infolist()
        all_names = [i.filename for i in members if not i.is_dir()]
        if len(members) != len(set(i.filename for i in members)):
            return ["Duplicate archive entries, including directories"]
        if any(i.flag_bits & 1 for i in members):
            return ["Encrypted archive members are not supported"]
        if any(i.file_size > 15_000_000 for i in members if not i.is_dir()):
            return ["Oversized RPT archive member"]
        if sum(i.file_size for i in members if not i.is_dir()) > 150_000_000:
            return ["RPT archive uncompressed size exceeds safety limit"]
        names = [name for name in all_names if name != "README.txt"]
        if len(all_names) != len(set(all_names)) or set(all_names) - {"README.txt"} != set(expected):
            return ["Unexpected or duplicate archive members"]
        if len(names) != 48 or len(set(names)) != 48 or set(names) != set(expected):
            return ["Expected exactly 48 v76 RPT documents with unique names"]
        for name, (state, year) in expected.items():
            try:
                with ZipFile(BytesIO(bundle.read(name))) as doc:
                    root = ET.fromstring(doc.read("word/document.xml"))
                text = " ".join(node.text or "" for node in root.iter()
                                if node.tag.endswith("}t"))
                checks = (
                    ("version", "v76 STAGING" in text),
                    ("state", "Negeri: " + state.replace("_", " ") in text),
                    ("year", "TAHUN " + str(year) in text),
                    ("calendar audit", "KPM/BKPP" in text),
                    ("complete PdP sequence", set(re.findall(r"PdP-(\d{3})", text))
                     == {f"{i:03}" for i in range(1, {4: 34, 5: 33, 6: 34}[year] + 1)}),
                )
                for label, valid in checks:
                    if not valid:
                        problems.append(name + ": missing " + label)
            except (OSError, ValueError, KeyError, ET.ParseError, BadZipFile, RuntimeError) as exc:
                problems.append(name + ": " + str(exc))
    return problems

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify_rpt_pj_2027_v76.py ARCHIVE.zip")
    failures = verify(Path(sys.argv[1]))
    for failure in failures:
        print(failure)
    print("PASS: 48 v76 RPT files" if not failures else "FAIL: " + str(len(failures)))
    raise SystemExit(bool(failures))
