#!/usr/bin/env python3
"""Guard all 270 Moral supplementary SP-specific teacher-developed tasks.

This checks individual source words, evidence hashes, content, release status,
scope and lesson structure. It does NOT convert topic/SP-based activities into
visually approved textbook activities or certify real Telegram delivery.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "audits/pendidikan_moral_supplement270_semantic_review_20261105.json"
BASE = ROOT / "rph_standalone/pendidikan_moral/pengukuhan"
APPROACHES = {"knowledge":70, "reasoning":70, "emotion":70, "practice":60}
SECTIONS = ("Set induksi", "Aktiviti 1", "Aktiviti 2",
            "Pengukuhan/Pentaksiran PBD", "Penutup")


def main() -> None:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    records = data["results"]
    assert len(records) == 270
    assert data["final_ready"] is False
    assert data["visual_activity_approval"] is False
    assert data["telegram_teacher_end_to_end"] is False
    assert Counter(r["approach"] for r in records) == APPROACHES
    assert Counter(r["year"] for r in records) == {year:54 for year in range(2,7)}
    assert len({(r["year"],r["session"]) for r in records}) == 270
    for r in records:
        y, number, unit = r["year"], r["session"], r["unit"]
        path = BASE / f"year{y}/sesi_{number:03d}.md"
        raw = path.read_text(encoding="utf-8")
        assert hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16] == r["new_sha256_16"], path
        assert r["new_sha256_16"] != r["source_sha256_16"], path
        assert f"**Unit:** {unit}." in raw, path
        assert "STATUS" in raw, path
        assert "siapa memerlukan apa" not in raw, path
        assert "bantuan/tindakan praktikal" not in raw, path
        assert any(x in raw.lower() for x in ("bukan semakan aktiviti individu", "halaman aktiviti", "bukan petikan buku", "pengesahan aktiviti di kelas")), path
        assert r["scenario"] in raw, path
        assert all(raw.count("**"+step+" (") == 1 for step in SECTIONS), path
        for field in ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Pengukuhan/Pentaksiran PBD", "Penutup"):
            line = next(x for x in raw.splitlines() if x.startswith("**"+field+" ("))
            assert len(line) >= 150 and "Guru" in line, (path, field)
            if field != "Pengukuhan/Pentaksiran PBD":
                assert "Murid" in line, (path, field)
            else:
                assert any(t in line for t in ("Murid", "individu", "diperagakan", "refleksi")), (path, field)
        for code in r["sp"]:
            assert code in raw and re.search(r"\b"+re.escape(code)+r"\b",raw), (path,code)
        assert "60 minit" in raw and "Kriteria kejayaan" in raw, path
        if y==6:
            assert "Semakan 2017" in raw and "2021" in raw, path
            assert "fliphtml5.com/sbinx/haph" in raw, path
            assert "buku teks" in raw.lower(), path
        # The versioned source record remains an educator proposal, not
        # official textbook task evidence or a release flag.
        assert r["evidence_scope"] == "DSKP_SP_AND_TEACHER_DEVELOPED_CLASSROOM_SCENE_NOT_VISUAL_BOOK_ACTIVITY", path
    print("PASS 270/270 individual supplementary SP and teaching-scenario checks")
    print("PASS 54/54 Year2, Year3, Year4, Year5, Year6 source files")
    print("PASS 70 knowledge + 70 reasoning + 70 emotion + 60 action; no generic 'siapa memerlukan apa'")
    print("NOT FINAL READY: this is individualized DSKP-aligned teacher-developed content, not full visual textbook/task proof or real Telegram teacher delivery.")


if __name__=="__main__":
    main()
