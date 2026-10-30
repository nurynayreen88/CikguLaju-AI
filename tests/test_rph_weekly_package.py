import unittest
from io import BytesIO
from zipfile import ZipFile
from rph_weekly_package import weekly_zip

class PackageTests(unittest.TestCase):
    def test_package(self):
        data=weekly_zip({"Isnin/1A_BM.docx":b"sample","Selasa/1B_BI.pdf":b"sample2"})
        with ZipFile(BytesIO(data)) as z:
            self.assertEqual(len(z.namelist()),2)
    def test_empty(self):
        with self.assertRaises(ValueError): weekly_zip({})
    def test_traversal(self):
        with self.assertRaises(ValueError): weekly_zip({"../secret.pdf":b"x"})
    def test_duplicate_case(self):
        with self.assertRaises(ValueError): weekly_zip({"A.pdf":b"x","a.PDF":b"x"})
if __name__=="__main__": unittest.main()
