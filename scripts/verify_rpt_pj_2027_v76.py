"""Validate 48 v76 Word files against their filename, state and year.

Usage: python scripts/verify_rpt_pj_2027_v76.py ARCHIVE.zip
Read-only; no changes to archive or application data.
"""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rpt_pj_2027_delivery import FILE_PATTERN, STATES, YEARS

def verify(archive):
    expected = {
        "RPT_PJ_2027_DOCX/" + FILE_PATTERN.format(state=state, year=year): (state, year)
        for state in STATES for year in YEARS
    }
    problems = []
    with ZipFile(archive) as bundle:
        names = [i.filename for i in bundle.infolist() if not i.is_dir() and i.filename != "README.txt"]
        if len(names) != 48 or set(names) != set(expected):
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
                )
                for label, valid in checks:
                    if not valid:
                        problems.append(name + ": missing " + label)
            except (OSError, ValueError, KeyError, ET.ParseError) as exc:
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
