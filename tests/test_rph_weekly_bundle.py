import unittest
from io import BytesIO
from zipfile import ZipFile
from rph_weekly_bundle import weekly_result_bundle

class BundleTests(unittest.TestCase):
    def test_bundle(self):
        result=weekly_result_bundle({"Isnin/1A.pdf":b"pdf"},[{"session_id":"a","status":"succeeded","detail":"OK"}])
        with ZipFile(BytesIO(result)) as z:
            self.assertIn("ringkasan_penjanaan.csv",z.namelist())
            self.assertIn("Isnin/1A.pdf",z.namelist())
    def test_formula_sanitized(self):
        result=weekly_result_bundle({"a.pdf":b"x"},[{"session_id":"a","status":"failed","detail":"=2+2"}])
        with ZipFile(BytesIO(result)) as z:
            self.assertIn("'=2+2",z.read("ringkasan_penjanaan.csv").decode("utf-8-sig"))
    def test_duplicate_rejected(self):
        rows=[{"session_id":"a","status":"succeeded","detail":"ok"}]*2
        with self.assertRaises(ValueError): weekly_result_bundle({"a.pdf":b"x"},rows)
    def test_invalid_status(self):
        with self.assertRaises(ValueError): weekly_result_bundle({"a.pdf":b"x"},[{"session_id":"a","status":"unknown","detail":"x"}])
if __name__=="__main__": unittest.main()
