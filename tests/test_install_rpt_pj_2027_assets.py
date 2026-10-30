import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.install_rpt_pj_2027_assets import install
from rpt_pj_2027_delivery import FILE_PATTERN, STATES, YEARS


class TestInstallRPTAssets(unittest.TestCase):
    def make_zip(self, archive):
        with zipfile.ZipFile(archive, "w") as z:
            for state in STATES:
                for year in YEARS:
                    z.writestr("RPT_PJ_2027_DOCX/" +
                               FILE_PATTERN.format(state=state, year=year),
                               b"example")

    def test_install_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "rpt.zip"
            self.make_zip(archive)
            target = root / "data"
            self.assertEqual(install(archive, target), 48)
            self.assertEqual(len(list((target / "RPT_PJ_2027_DOCX").glob("*.docx"))), 48)
            with self.assertRaises(FileExistsError):
                install(archive, target)

    def test_preflight_existing_file_prevents_partial_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "rpt.zip"
            self.make_zip(archive)
            target = root / "data" / "RPT_PJ_2027_DOCX"
            target.mkdir(parents=True)
            existing = target / FILE_PATTERN.format(state="WP_Putrajaya", year=6)
            existing.write_bytes(b"original")
            with self.assertRaises(FileExistsError):
                install(archive, root / "data")
            self.assertEqual(existing.read_bytes(), b"original")
            self.assertEqual(len(list(target.glob("*.docx"))), 1)


if __name__ == "__main__":
    unittest.main()
