#!/usr/bin/env python3
"""Non-destructive staging regression for correct Sejarah textbook editions."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {4: ("978-983-49-2472-0", "DBP 2019, KSSR Semakan 2017"),
            5: ("978-983-49-2829-2", "DBP 2020, KSSR Semakan 2017"),
            6: ("978-983-49-3279-4", "DBP 2021, KSSR Semakan 2017")}
LEGACY_2016_YEAR6 = "978-983-49-0269-8"
count = 0
for year, (isbn, edition) in EXPECTED.items():
    mapping = json.loads((ROOT / f"curriculum/sejarah/y{year}_buku_teks_unit_map_20261106.json").read_text())
    lessons = json.loads((ROOT / f"rph_standalone/sejarah/y{year}_2027_rph_DRAF.json").read_text())["lessons"]
    assert (mapping["isbn"], mapping["edition"]) == (isbn, edition)
    assert all((u["isbn"], u["edition"]) == (isbn, edition) for u in mapping["units"])
    assert len(lessons) == 36
    for row in lessons:
        r = row["rph"]
        ref = r["textbook_reference"]
        assert (ref["isbn"], ref["edition"]) == (isbn, edition), row["id"]
        assert LEGACY_2016_YEAR6 not in r["bbm"], row["id"]
        assert r["status"].startswith("DRAF")
        assert not r["teacher_approval"] and not r["textbook_page_verified"]
        count += 1
assert count == 108
print(f"Sejarah ISBN/edition guard: {count}/108 correct; Year 6 2016 legacy disallowed")
