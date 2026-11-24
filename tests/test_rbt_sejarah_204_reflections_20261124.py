"""All 204 source rows, not approval or actual PDF layout claims."""
import re
from web import rbt_2027_user_runtime as rbt
from web import sejarah_2027_user_runtime as sej

def test_all_204_native_rows():
    total = 0
    for module, count in ((rbt, 32), (sej, 36)):
        for year in (4, 5, 6):
            for pdp in range(1, count+1):
                row = module._lesson(year, pdp)
                assert row is not None
                is_rbt = module is rbt
                raw = row if is_rbt else row["rph"]
                state = {"subject": module.SUBJECT, "year": f"Tahun {year}", "lesson_no": str(pdp),
                    "sk_code": raw["sk"][0] if is_rbt else raw["sk"],
                    "sp_code": raw["sp_codes"][0], module.SELECTION: {"year": year, "pdp": pdp}}
                previous = {"KELAS": "", "TARIKH": "", "MASA": ""}
                result = module.adapt_rows(state, previous)
                assert result is not previous
                assert all(result[k] == "" for k in previous)
                criterion = raw["kriteria_kejayaan"] if is_rbt else raw["success_criteria"]
                evidence = " ".join(criterion.split()).split("; guru menilai",1)[0].rstrip(".; ")
                evidence = re.sub(r"^Murid (?:dapat )?", "", evidence, flags=re.I)
                assert evidence in result["REFLEKSI"]
                assert result["REFLEKSI"].startswith("____ / ____")
                assert result["KRITERIA KEJAYAAN"] == criterion
                assert "DRAF" in result["TAJUK"]
                assert not re.search(r"\bPdP\s+\d+", result["TAJUK"], re.I)
                for key in ("STANDARD KANDUNGAN","STANDARD PEMBELAJARAN","OBJEKTIF PEMBELAJARAN","AKTIVITI UTAMA","SET INDUKSI","PENUTUP"):
                    assert result[key]
                assert module.adapt_rows(dict(state, rph_teacher_reflection="Catatan guru."), previous)["REFLEKSI"] == "Catatan guru."
                total += 1
    assert total == 204
