"""Exercise transactional rollback of a failed RPT archive extraction."""
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from rpt_pj_2027_delivery import FILE_PATTERN, STATES, YEARS
from scripts.install_rpt_pj_2027_assets import install


class RPTInstallRollbackTests(unittest.TestCase):
    def test_copy_failure_leaves_no_partial_release(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            archive = base / "fixture.zip"
            docbuf = io.BytesIO()
            with ZipFile(docbuf, "w") as doc:
                doc.writestr("[Content_Types].xml", "<Types/>")
                doc.writestr("word/document.xml", "<document/>")
            with ZipFile(archive, "w") as bundle:
                for state in STATES:
                    for year in YEARS:
                        name = "RPT_PJ_2027_DOCX/" + FILE_PATTERN.format(
                            state=state, year=year)
                        bundle.writestr(name, docbuf.getvalue())
            destination = base / "new_release"
            with patch("scripts.install_rpt_pj_2027_assets.shutil.copyfileobj",
                       side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    install(archive, destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
