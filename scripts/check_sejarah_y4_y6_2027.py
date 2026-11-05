#!/usr/bin/env python3
"""Non-destructive checks for Sejarah Year 4–6 2027 staging assets."""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {4: (11, 76), 5: (12, 84), 6: (10, 68)}
for y, (num_sk, num_sp) in EXPECTED.items():
    cross = json.loads((ROOT/f"curriculum/sejarah/y{y}_dskp_crosswalk_DRAF.json").read_text())
    obj = json.loads((ROOT/f"rph_standalone/sejarah/y{y}_2027_rph_DRAF.json").read_text())
    rpt = list(csv.DictReader((ROOT/f"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{y}_2027_A_B_DRAF.csv").open()))
    lesson = obj["lessons"]
    assert len(cross["standards"]) == num_sk
    specs = [sp["code"] for s in cross["standards"] for sp in s["sp"]]
    assert len(specs) == num_sp and len(set(specs)) == num_sp
    assert len(lesson) == len(rpt) == 36
    assert sum(x["rph"]["type"] == "KANDUNGAN" for x in lesson) == 32
    assert sum(x["rph"]["type"] == "KAJIAN_KES" for x in lesson) == 4
    seen = {code for x in lesson if x["rph"]["type"] == "KANDUNGAN" for code in x["rph"]["sp_codes"]}
    assert not (set(specs) - seen), set(specs) - seen
    from datetime import date
    previous_a = previous_b = None
    unit_map = json.loads((ROOT/f"curriculum/sejarah/y{y}_buku_teks_unit_map_20261106.json").read_text())
    units = {u["sk"]:u for u in unit_map["units"]}
    assert len(units) == num_sk and set(units) == {s["sk"] for s in cross["standards"]}
    assert len({u["number"] for u in units.values()}) == num_sk
    for i, x in enumerate(lesson, 1):
        a0 = date.fromisoformat(x["weeks"]["A"]["start"])
        a1 = date.fromisoformat(x["weeks"]["A"]["end"])
        b0 = date.fromisoformat(x["weeks"]["B"]["start"])
        b1 = date.fromisoformat(x["weeks"]["B"]["end"])
        assert 0 <= (a1 - a0).days <= 4, ("Kumpulan A minggu bertindih", y, i)
        assert 0 <= (b1 - b0).days <= 4, ("Kumpulan B minggu bertindih", y, i)
        assert a0.weekday() in (6, 0) and a1.weekday() in (0, 1, 2, 3)
        assert b0.weekday() == 0 and b1.weekday() in (2, 3, 4)
        if previous_a: assert a0 > previous_a
        if previous_b: assert b0 > previous_b
        previous_a, previous_b = a1, b1
        r = x["rph"]
        bt = r["textbook_reference"]
        u = units[r["sk"]]
        assert r["unit_toc_verified"] is True
        assert r["textbook_page_verified"] is False and r["teacher_approval"] is False
        assert bt["unit_number"] == u["number"]
        assert bt["unit_title"] == u["name"]
        assert bt["unit_start_page"] == u["start"]
        assert bt["unit_end_page"] == u["end"]
        assert bt["isbn"] == unit_map["isbn"]
        assert bt["exact_activity_page_confirmed"] is False
        assert "Buku Teks" in r["bbm"] and "julat unit" in r["bbm"]
        assert "Murid" in r["aktiviti_1"]["activity"] and "Guru" in r["aktiviti_1"]["activity"]
        assert "Murid" in r["aktiviti_2"]["activity"] and "Guru" in r["aktiviti_2"]["activity"]
        assert r["status"].startswith("DRAF")
        assert x["num"] == i == int(rpt[i - 1]["PdP"])
        assert x["id"] == rpt[i - 1]["ID"]
        assert r["year"] == y and r["academic_year"] == 2027
        assert not r["textbook_page_verified"] and not r["teacher_approval"]
        assert set(r["sp_codes"]).issubset(set(specs))
        assert sum(r[k]["min"] for k in ("set_induksi","aktiviti_1","aktiviti_2","pengukuhan_pbd","penutup")) == 60
        assert all(r[k]["activity"] for k in ("set_induksi","aktiviti_1","aktiviti_2","pengukuhan_pbd","penutup"))
        assert x["weeks"]["A"]["start"] == rpt[i-1]["Kumpulan A minggu mula"]
        assert x["weeks"]["B"]["start"] == rpt[i-1]["Kumpulan B minggu mula"]
        path = ROOT/f"rph_standalone/sejarah/tahun_{y}/RPH_{x['id']}.md"
        assert path.is_file() and "Set Induksi" in path.read_text()
    assert all(row["Unit Buku Teks"] == units[lesson[i]["rph"]["sk"]]["name"] for i, row in enumerate(rpt))
    assert (ROOT/f"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{y}_2027_A_B_DRAF.html").is_file()
    assert (ROOT/f"rph_standalone/sejarah/RPH_SEJARAH_TAHUN_{y}_2027_DRAF.html").is_file()
    print(f"Tahun {y}: {num_sk} SK / {num_sp} SP / 36 PdP / 36 RPH — LULUS semakan struktur")
print("Nota: semakan struktur BUKAN pengesahan halaman buku teks, pedagogi individu, PDF Word atau Telegram.")
