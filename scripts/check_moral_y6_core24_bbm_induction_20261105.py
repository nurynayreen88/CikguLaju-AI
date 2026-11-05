#!/usr/bin/env python3
"""Guard source-grade BBM and inductions of 24 Moral Year6 core RPH.

This checks source chapter/edition and DSKP links only; it is not a claim that
all activities were visually compared to the 2021 textbook or taught.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID_SET = set(range(13, 19)) | set(range(22, 40))
RPH = ROOT / "rph_standalone/pendidikan_moral/year6"
AUDIT = ROOT / "audits/pendidikan_moral_y6_kssr2017_edition_migration_20261105.json"


def main() -> None:
    data = json.loads(AUDIT.read_text(encoding="utf-8"))
    mapped = {x["lesson"]: x for x in data["revised_topic_mapped_core"]}
    assert ID_SET <= mapped.keys(), "Missing current-edition mapping"
    for n in sorted(ID_SET):
        r = mapped[n]
        unit = r["unit"]
        start, end = r["printed_pages"]
        source = (RPH / f"lesson_{n:03d}.md").read_text(encoding="utf-8")
        assert "STATUS: DRAF SEMAK — BELUM READY" in source, n
        assert "Rekod audit sejarah" in source and "Batasan bukti sejarah" in source, n
        bbm = re.search(r"^\\*\\*BBM:\\*\\* (.+)$", source, re.M)
        induction = re.search(r"^\\*\\*Set induksi \\(5 minit\\):\\*\\* (.+)$", source, re.M)
        activity1 = re.search(r"^\\*\\*Aktiviti 1 \\(20 minit\\) — ([^:]+):\\*\\* (.+)$", source, re.M)
        assert bbm and induction and activity1, (n, "missing teaching step")
        heading = activity1.group(1)
        assert f"Unit {unit}, m/s {start}–{end} (bahagian **{heading}**)" in bbm.group(1), n
        assert "KSSR Semakan 2017 (DBP 2021)" in bbm.group(1), n
        assert f"**{heading}**" in induction.group(1) and f"m/s {start}" in induction.group(1), n
        assert "Murid" in induction.group(1) and "Guru" in induction.group(1), n
        assert f"m/s {start}–{end}" in activity1.group(2), n
        assert f"Unit {unit}, m/s {start}–{end}" in source, n
        assert all(code in source for code in r["sp_codes"]), (n, "SP mismatch")
    assert len(ID_SET) == 24
    print("PASS 24/24 Year6 BBM, textbook edition, page-linked inductions and SP; all stay DRAFT.")
    print("NOT FINAL READY: chapter/text-task provenance does not equal visual page approval or live Telegram delivery.")


if __name__ == "__main__":
    main()
