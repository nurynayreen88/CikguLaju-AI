"""Guard against accidentally auditing a different DB than Telegram uses."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeMathsCanonicalSourceContract(unittest.TestCase):
    def test_app_reads_the_exact_math_v25_99_source(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        start = source.index("def _sm2542_rows(")
        end = source.index("\ndef _sm2542_unique_units(", start)
        method = source[start:end]
        self.assertIn("if subject=='Matematik':", method)
        self.assertIn("con=_sqlite3.connect(_math_v2599_db_path())", method)
        self.assertIn("table='verified_pdp_sequence_v2'", method)
        self.assertIn("table='verified_pdp_sequence'", method)  # Sains branch, NOT Math
        self.assertIn("COALESCE(pdp_sequence_code,'')<>''", method)
        self.assertIn("ORDER BY COALESCE(source_sequence_no,9999), id", method)
        self.assertIn("REJECT_NON_SK", method)
        self.assertIn("SOURCE_NONCORE", method)

    def test_source_manifest_matches_runtime_digest(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        start = source.index("def _math_v2599_db_path():")
        end = source.index("\ndef _sm2542_rows(", start)
        text = source[start:end]
        self.assertIn(
            "74f1e139ae6e7f64379ee3fb103334f450c683152186b03368bb02dfe3b8c821",
            text,
        )
        self.assertIn("CikguLaju_Curriculum_Master_v25_99_MATH_T1_T6_CANONICAL", text)
        self.assertIn('part{i:02d}', text)


if __name__ == "__main__":
    unittest.main()
