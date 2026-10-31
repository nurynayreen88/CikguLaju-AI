import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO

from rpt_pj_2027_delivery import FILE_PATTERN, STATES, YEARS
from scripts.verify_rpt_pj_2027_v76 import verify


class TestV76Verifier(unittest.TestCase):
    def test_reject_incorrect_version_in_content(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "bad.zip"
            buffer = BytesIO()
            with ZipFile(buffer, "w") as doc:
                doc.writestr("word/document.xml", "<document><t>v75 STAGING</t></document>")
            with ZipFile(archive, "w") as bundle:
                for state in STATES:
                    for year in YEARS:
                        name = "RPT_PJ_2027_DOCX/" + FILE_PATTERN.format(state=state, year=year)
                        bundle.writestr(name, buffer.getvalue())
            problems = verify(archive)
            self.assertGreaterEqual(len(problems), 48)


if __name__ == "__main__":
    unittest.main()
