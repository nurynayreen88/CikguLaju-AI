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
    audit_path = ROOT/"audits/sejarah_y4_y6_sp_specific_11rph_20261106.json"
    audit = json.loads(audit_path.read_text())
    assert audit["count"] == 11
    matrix = json.loads((ROOT/"curriculum/sejarah/sejarah_97_rph_aktiviti_sp_context_20261106.json").read_text())
    assert matrix["total"] == 97 and len(matrix["records"]) == 97
    all_matrix = {m["id"]:m for m in matrix["records"]}
    assert len(all_matrix) == 97
    assert len([m for m in matrix["records"] if m["year"] == y]) == (33 if y == 6 else 32)
    audited = {a["id"]:a for a in audit["rows"]}
    assert len(audited) == 11
    calendar = json.loads((ROOT/"curriculum/sejarah/kalender_sejarah_2027_kumpulan_a_b.json").read_text())
    assert calendar["academic_year"] == 2027
    assert len(calendar["weeks"]["A"]) == len(calendar["weeks"]["B"]) == 36
    assert calendar["planned_annual_hours"] >= calendar["min_annual_hours"]
    for i, x in enumerate(lesson, 1):
        assert x["weeks"] == {"A":calendar["weeks"]["A"][i-1],"B":calendar["weeks"]["B"][i-1]}
        a0 = date.fromisoformat(x["weeks"]["A"]["start"])
        a1 = date.fromisoformat(x["weeks"]["A"]["end"])
        b0 = date.fromisoformat(x["weeks"]["B"]["start"])
        b1 = date.fromisoformat(x["weeks"]["B"]["end"])
        assert 0 <= (a1 - a0).days <= 4, ("Kumpulan A minggu bertindih", y, i)
        assert 0 <= (b1 - b0).days <= 4, ("Kumpulan B minggu bertindih", y, i)
        assert a0.weekday() in (6, 0) and a1.weekday() in (0, 1, 2, 3)
        assert b0.weekday() == 0 and b1.weekday() in (2, 3, 4)
        assert x["weeks"]["A"]["start"] not in calendar["full_week_closed"]["A"]
        assert x["weeks"]["B"]["start"] not in calendar["full_week_closed"]["B"]
        assert x["weeks"]["A"]["start"] != "2027-03-14"
        for group in ("A", "B"):
            day0 = date.fromisoformat(x["weeks"][group]["start"])
            day1 = date.fromisoformat(x["weeks"][group]["end"])
            for left,right in calendar["term_breaks"][group]:
                assert day1 < date.fromisoformat(left) or day0 > date.fromisoformat(right), ("RPT weeks overlap term holiday",y,i,group)
        if previous_a: assert a0 > previous_a
        if previous_b: assert b0 > previous_b
        previous_a, previous_b = a1, b1
        r = x["rph"]
        if x["id"] in all_matrix:
            m = all_matrix[x["id"]]
            context = r["context_specific_activity"]
            assert m["year"] == y and m["number"] == i
            assert all(context[k] == m[v] for k, v in (("stimulus","stimulus"),("task1","task1"),("task2","task2"),("pbd_evidence","pbd_evidence")))
            assert r["status"] == "DRAF_97_AKTIVITI_KHUSUS_SELESAI_SEMAKAN_BUKU_BELUM_LULUS"
            assert context["exact_textbook_exercise_checked"] is False and context["teacher_approval"] is False
            assert context["quality_state"].startswith("DRAF")
            assert m["task1"] in r["aktiviti_1"]["activity"]
            assert m["task2"] in r["aktiviti_2"]["activity"]
            assert m["pbd_evidence"] in r["pengukuhan_pbd"]["activity"]
            assert "Guru" in r["set_induksi"]["activity"] and "Murid" in r["set_induksi"]["activity"]
            assert "Guru" in r["penutup"]["activity"] and "Murid" in r["penutup"]["activity"]
            assert r["aktiviti_1"]["activity"] != r["aktiviti_2"]["activity"]
            assert len(r["success_criteria"]) > 70
        if x["id"] in audited:
            ev = r["page_specific_evidence"]
            target = audited[x["id"]]
            assert ev["pages"] == target["pages"] and ev["sources"] == target["sources"]
            assert ev["level"] == target["evidence"]
            assert ev["teacher_validated"] is False and ev["exact_textbook_activity_approved"] is False
            assert ev["actual_textbook_visual_page_checked"] is False
            assert ev["textbook_html_page_text_read"] is (y == 5)
            assert r["status"].startswith("DRAF")
        assert ".." not in r["aktiviti_1"]["activity"] and ".." not in r["aktiviti_2"]["activity"]
        if r.get("context_specific_activity") and r["values_sp"]:
            civic = r["values_sp"][0]["text"].rstrip(".")
            expected = "Murid " + civic[0].lower() + civic[1:] + "."
            assert expected in r["aktiviti_2"]["activity"], ("civic action mismatch", x["id"])
            assert r["aktiviti_1"]["activity"] != r["aktiviti_2"]["activity"]
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
        assert "Buku Teks" in r["bbm"] and ("julat unit" in r["bbm"] or "julat isi kandungan" in r["bbm"])
        assert "Murid" in r["aktiviti_1"]["activity"] and "Guru" in r["aktiviti_1"]["activity"]
        assert "Murid" in r["aktiviti_2"]["activity"] and "Guru" in r["aktiviti_2"]["activity"]
        assert r["status"].startswith("DRAF")
        assert x["num"] == i == int(rpt[i - 1]["PdP"])
        assert x["id"] == rpt[i - 1]["ID"]
        expected_evidence = (r.get("context_specific_activity") or {}).get("pbd_evidence") or r["pengukuhan_pbd"]["activity"]
        assert rpt[i - 1]["Evidens PBD RPH"] == expected_evidence
        assert rpt[i - 1]["Tahap Pemurnian"] == ("KHUSUS_SP_DRAF" if r.get("context_specific_activity") else "HALAMAN_RUJUKAN_DRAF")
        assert r["year"] == y and r["academic_year"] == 2027
        assert not r["textbook_page_verified"] and not r["teacher_approval"]
        assert set(r["sp_codes"]).issubset(set(specs))
        assert sum(r[k]["min"] for k in ("set_induksi","aktiviti_1","aktiviti_2","pengukuhan_pbd","penutup")) == 60
        assert all(r[k]["activity"] for k in ("set_induksi","aktiviti_1","aktiviti_2","pengukuhan_pbd","penutup"))
        assert x["weeks"]["A"]["start"] == rpt[i-1]["Kumpulan A minggu mula"]
        assert x["weeks"]["B"]["start"] == rpt[i-1]["Kumpulan B minggu mula"]
        path = ROOT/f"rph_standalone/sejarah/tahun_{y}/RPH_{x['id']}.md"
        assert path.is_file() and "Set Induksi" in path.read_text()
    assert all((x["id"] in all_matrix) ^ (x["id"] in audited) for x in lesson)
    assert len({(x["rph"].get("context_specific_activity") or {}).get("pbd_evidence") for x in lesson if x["id"] in all_matrix}) == (33 if y == 6 else 32)
    assert all(row["Unit Buku Teks"] == units[lesson[i]["rph"]["sk"]]["name"] for i, row in enumerate(rpt))
    assert (ROOT/f"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{y}_2027_A_B_DRAF.html").is_file()
    html = (ROOT/f"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{y}_2027_A_B_DRAF.html").read_text()
    assert "<th>Tajuk / SK / Buku Teks</th>" in html
    assert "<th>Fokus SP / Evidens PBD</th>" in html
    assert html.count("<strong>Evidens PBD:</strong>") == 72
    for u in units.values():
        assert f"Unit {u['number']}: {u['name']}" in html

    assert (ROOT/f"rph_standalone/sejarah/RPH_SEJARAH_TAHUN_{y}_2027_DRAF.html").is_file()
    print(f"Tahun {y}: {num_sk} SK / {num_sp} SP / 36 PdP / 36 RPH — LULUS semakan struktur")
print("Semakan matriks 97/97 aktiviti spesifik termasuk variasi, 11 RPH asal, SP, dokumen sumber: LULUS struktur.")
print("Nota: semakan struktur BUKAN pengesahan halaman buku teks, pedagogi individu, PDF Word atau Telegram.")
