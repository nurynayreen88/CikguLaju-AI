"""All 204 source-backed RPH row adaptations; no source mutation."""
import re
from web import rbt_2027_user_runtime as rbt
from web import sejarah_2027_user_runtime as sej


def test_all_204():
    count = 0
    for module, total in ((rbt, 32), (sej, 36)):
        for year in (4, 5, 6):
            for pdp in range(1, total + 1):
                row = module._lesson(year, pdp)
                assert row, (module.SUBJECT, year, pdp)
                plan = row if module is rbt else row["rph"]
                criterion = plan["kriteria_kejayaan"] if module is rbt else plan["success_criteria"]
                sk = plan["sk"][0] if module is rbt else plan["sk"]
                state = {"subject":module.SUBJECT,"year":f"Tahun {year}",
                         "lesson_no":str(pdp),"sk_code":sk,"sp_code":plan["sp_codes"][0],
                         module.SELECTION:{"year":year,"pdp":pdp}}
                original = {"KELAS":"4 Bestari","TARIKH":"","MASA":"","REFLEKSI":"original"}
                out = module.adapt_rows(state, original)
                evidence = re.split(r";\s*guru menilai\b", criterion.strip(), maxsplit=1, flags=re.I)[0].rstrip(". ")
                assert evidence in out["REFLEKSI"], (module.SUBJECT,year,pdp)
                assert out["REFLEKSI"].startswith("____ / ____")
                assert out["KRITERIA KEJAYAAN"] == criterion
                if module is rbt:
                    bbm = out["BAHAN BANTU MENGAJAR"]
                    if year == 4 and pdp in (1, 2, 3):
                        assert bbm == row["bbm"], (year,pdp,bbm)
                        assert "Buku Teks hlm." in bbm
                    else:
                        assert "cadangan halaman, perlu semak visual" in bbm
                    assert not row["review"]["release_ready"]
                assert out["KELAS"] == original["KELAS"] and out["TARIKH"] == ""
                assert "DRAF" in out["TAJUK"]
                assert not re.search(r"PdP\s+\d{3}\b",out["TAJUK"],re.I)
                assert "Aktiviti 1\n" in out["AKTIVITI UTAMA"] and "Aktiviti 2\n" in out["AKTIVITI UTAMA"]
                assert module.adapt_rows({**state,"rph_teacher_reflection":"Catatan guru."},original)["REFLEKSI"] == "Catatan guru."
                assert module.adapt_rows({**state,"rph_reflection_mode":"manual"},original)["REFLEKSI"] == ""
                assert original["REFLEKSI"] == "original"
                count += 1
    assert count == 204
