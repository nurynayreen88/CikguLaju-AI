import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO

from rpt_pj_2027_delivery import FILE_PATTERN, STATES, YEARS
from scripts.verify_rpt_pj_2027_v76 import verify


def sample_doc():
    doc = BytesIO()
    with ZipFile(doc, "w") as z:
        z.writestr("word/document.xml", "<document><t>v75 STAGING</t></document>")
    return doc.getvalue()


class TestV76ArchiveValidation(unittest.TestCase):
    def test_duplicate_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "duplicate.zip"
            with ZipFile(archive, "w") as bundle:
                for state in STATES:
                    for year in YEARS:
                        name = "RPT_PJ_2027_DOCX/" + FILE_PATTERN.format(state=state, year=year)
                        bundle.writestr(name, sample_doc())
                duplicate = "RPT_PJ_2027_DOCX/" + FILE_PATTERN.format(state=STATES[0], year=YEARS[0])
                bundle.writestr(duplicate, sample_doc())
            self.assertEqual(len(verify(archive)), 1)


if __name__ == "__main__":
    unittest.main()
