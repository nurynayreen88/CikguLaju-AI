"""Offline 480-session Moral source and presentation regression."""
import re
from web.moral_rpt_rph_source import STATE_KEY, load_plan
from web.pendidikan_moral_80_runtime import adapt_rows


def test_all_480():
    count = 0
    linked = 0
    for year in range(2, 7):
        for number in range(1, 97):
            plan = load_plan(year, number)
            assert plan is not None, (year, number)
            state = {"subject": "Pendidikan Moral", "year": f"Tahun {year}",
                     "lesson_no": str(number), STATE_KEY: number}
            base = {"KELAS": "", "REFLEKSI": "____ / ____ murid mencapai objektif."}
            result = adapt_rows(state, base)
            assert not re.match(r"PdP\s+\d+", result["TAJUK"], re.I)
            assert plan["title"].startswith(f"PdP {number:03d}")
            for key, value in plan["fields"].items():
                if key != "TAJUK":
                    assert result[key] == value, (year, number, key)
            assert result["KELAS"] == ""
            assert base["REFLEKSI"] == "____ / ____ murid mencapai objektif."
            if result["REFLEKSI"] != base["REFLEKSI"]:
                linked += 1
                assert result["REFLEKSI"].startswith("____ / ____ murid mencapai sasaran: ")
            assert adapt_rows({**state, "rph_teacher_reflection":"Catatan guru."}, base)["REFLEKSI"] == "Catatan guru."
            assert adapt_rows({**state, "rph_reflection_mode":"manual"}, base)["REFLEKSI"] == ""
            count += 1
    assert count == 480
    assert linked == 480, f"{linked}/480 source-linked reflections"
