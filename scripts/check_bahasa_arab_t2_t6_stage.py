#!/usr/bin/env python3
"""Read-only source/first-PdP checks for Bahasa Arab Years 2–6 staging.

This is NOT a release test. It verifies that staging explicitly stays non-LIVE.
Run from repository root: python scripts/check_bahasa_arab_t2_t6_stage.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = ROOT / "rph_standalone" / "bahasa_arab"
MANIFEST = SUBJECT / "source_manifest_20261105.json"
REQUIRED = (
    "Set induksi", "Aktiviti 1", "Aktiviti 2",
    "Pengukuhan / Penilaian", "Penutup", "BBM",
    "Kriteria kejayaan", "Refleksi guru", "BELUM READY",
)
EXPECTED_FOCUS = {
    2: ("هيا نتعارف", "ل", "ي"),
    3: ("تفضل إلى الفصل", "خ", "ش"),
    4: ("الشهور الميلادية", "ال"),
    5: ("في المطبخ", "ث", "س", "ص"),
    6: ("حياتنا أجمل بالنظافة", "ع", "أ", "ح", "ه"),
}


def check() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["release_status"] == "DRAF_STAGING_SAHAJA"
    assert data["total_final_ready_rph"] == 0
    for flag in ("production_db_touched", "telegram_live_touched", "web_live_touched"):
        assert data[flag] is False, f"Unexpected live flag: {flag}"
    assert sorted(data["years"]) == ["2", "3", "4", "5", "6"]
    for y in range(2, 7):
        src = data["years"][str(y)]
        assert src["provisional_rph_count"] == 6
        assert src["dskp"]["url"].startswith("https://")
        assert src["textbook"]["url"].startswith("https://")
        assert src["rpt_2026"].startswith("https://")
        assert src["textbook"]["source_page_verified"] is False
        for lesson_num in range(1, 7):
            p = SUBJECT / f"year{y}" / f"lesson_{lesson_num:03d}.md"
            txt = p.read_text(encoding="utf-8")
            if lesson_num > 1:
                assert "DRAF" in txt and "BELUM READY" in txt
                assert all(s in txt for s in ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Penutup", "PBD"))
                assert "muka surat" in txt.lower() or "halaman" in txt.lower()
                continue
        assert f"Bahasa Arab Tahun {y}" in txt
        assert "DSKP SK/SP:** 1.1 / 1.1.1" in txt
        assert all(section in txt for section in REQUIRED), p
        assert all(fragment in txt for fragment in EXPECTED_FOCUS[y]), p
        assert src["rpt_2026"] in txt
        assert "DRAF_STAGING" in txt and "BUKAN bahan LIVE" in txt
        assert len(txt) >= 1300, f"Suspiciously short first PdP: {p}"
    assert len(data["years"]["4"]["textbook_units_confirmed"]) == 4
    assert len(data["years"]["5"]["textbook_units_confirmed"]) == 4
    assert data["years"]["3"]["textbook"]["text_extractable"] is False
    assert data["years"]["6"]["dskp"]["text_extractable"] is False
    print("BA Year 2–6: 5 source entries / 30 draft first-six-PdP checks passed.")
    print("RELEASE BLOCKED: 0 final-ready; individual textbook/DSKP/RPT evidence outstanding.")


if __name__ == "__main__":
    check()
