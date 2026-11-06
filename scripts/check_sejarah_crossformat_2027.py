#!/usr/bin/env python3
"""Staging-only: assert 108 Sejarah RPH are identical across JSON/Markdown/HTML."""
from html import unescape
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
GENERIC_1 = "Guru membimbing murid menyemak sumber serta istilah Sejarah yang berkaitan."
GENERIC_2 = re.compile(r"Guru menyoal hubungan fakta, konteks masa atau tempat dalam Unit \\d+\\.")
modified = 0
seen = set()
for year in (4, 5, 6):
    obj = json.loads((ROOT / f"rph_standalone/sejarah/y{year}_2027_rph_DRAF.json").read_text(encoding="utf-8"))
    rendered_html = unescape((ROOT / f"rph_standalone/sejarah/RPH_SEJARAH_TAHUN_{year}_2027_DRAF.html").read_text(encoding="utf-8"))
    assert len(obj["lessons"]) == 36
    for lesson in obj["lessons"]:
        rph = lesson["rph"]
        ident = lesson["id"]
        assert ident not in seen and ident == rph["id"]
        seen.add(ident)
        md_path = ROOT / f"rph_standalone/sejarah/tahun_{year}/RPH_{ident}.md"
        md = md_path.read_text(encoding="utf-8")
        for key in ("aktiviti_1", "aktiviti_2", "pengukuhan_pbd"):
            content = rph[key]["activity"]
            assert content in md, ("Markdown differs from JSON", ident, key)
            assert content in rendered_html, ("HTML differs from JSON", ident, key)
        scope = rph["textbook_reference"]["checked_focus_pages"]
        assert scope["text_checked"] is True
        assert scope["teacher_approved"] is False
        assert scope["exact_exercise_visual_verification"] is False
        ev = rph["page_specific_evidence"]
        assert ev["actual_textbook_visual_page_checked"] is False
        assert ev["exact_textbook_activity_approved"] is False
        assert ev["teacher_validated"] is False
        assert not rph["teacher_approval"] and not rph["textbook_page_verified"]
        assert rph["status"].startswith("DRAF")
        if rph.get("context_specific_activity"):
            modified += 1
            assert ev["level"] == "TEXTBOOK_DIGITAL_TOPIC_CROSSWALK_NOT_VISUAL_EXERCISE", ident
            assert ev["pages"] == scope["printed_page_range"], ident
            assert ev["sources"] == scope["source_urls"], ident
            assert GENERIC_1 not in rph["aktiviti_1"]["activity"], ident
            assert not GENERIC_2.search(rph["aktiviti_2"]["activity"]), ident
            assert "hlm. " in rph["aktiviti_1"]["activity"], ident
            assert "hlm. " in rph["aktiviti_2"]["activity"], ident
assert len(seen) == 108
assert modified == 97, modified
print(f"Sejarah staging crossformat: {len(seen)}/108 JSON–Markdown–HTML aligned; {modified}/97 evidence-guided; 0 released")
