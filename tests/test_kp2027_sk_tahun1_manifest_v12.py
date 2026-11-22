"""Release contract for 4 verified-curriculum, non-live KP2027 SK Year 1 subjects."""
import os
import unittest
from pathlib import Path
from web import kp2027_sk_tahun1_manifest_v12 as m

class TestKP2027Year1SourceGate(unittest.TestCase):
    def test_exact_four_subjects_and_group_totals(self):
        self.assertEqual(set(m.PACKS),{"ALAM","MATH","BM_SK","PJ"})
        self.assertEqual([m.PACKS[s]["files"] for s in ("ALAM","MATH","BM_SK","PJ")],[64,249,353,127])
        self.assertEqual(sum(m.PACKS[s]["files"] for s in m.PACKS),793)
        self.assertEqual(sum(sum(m.PACKS[s]["groups"].values()) for s in m.PACKS),857)

    def test_qa_never_downloadable_even_with_approval_flag(self):
        for s in m.PACKS:
            for fmt in ("word","pdf"):
                with self.assertRaises(m.UnreleasedKP2027):
                    m.get_download(subject=s,group="A",lesson=1,file_format=fmt,
                                   account={"authenticated":True,"rakan_pembangun":True},approved=True)

    def test_strict_year_group_lesson_format_and_source(self):
        for s in m.PACKS:
            for group,limit in m.PACKS[s]["groups"].items():
                for bad in (0,-1,limit+1,True,"001","../passwd"):
                    with self.assertRaises(ValueError):
                        m.get_download(subject=s,group=group,lesson=bad,file_format="pdf")
        for s in ("", "PI", "MATH_DLP", None):
            with self.assertRaises(ValueError): m.pack_spec(s)
        with self.assertRaises(ValueError): m.get_download(subject="MATH",group="Z",lesson=1,file_format="pdf")
        with self.assertRaises(ValueError): m.get_download(subject="MATH",group="A",lesson=1,file_format="zip")

    def test_unrecognized_bytes_are_not_private_assets(self):
        for s in m.PACKS:
            with self.assertRaises(m.UnreleasedKP2027):m.verify_qa_zip(s,b"not archive")

    def test_actual_qa_packages_integrity_when_mounted(self):
        root=os.environ.get("KP2027_V12_QA_DIR")
        if not root or not Path(root).exists():self.skipTest("Source QA archive not in CI")
        paths={
          "ALAM":"CIKGULAJU_KP2027_ALAM_T1_64_LESSON_V10_19_GABUNG_SP_WORD_PDF_QA_20261122.zip",
          "MATH":"CIKGULAJU_KP2027_MATEMATIK_T1_249_LESSON_A125_B124_V11_WORD_PDF_QA_20261122.zip",
          "BM_SK":"CIKGULAJU_KP2027_BM_SK_T1_353_LESSON_V12_WORD_PDF_QA_20261122.zip",
          "PJ":"CIKGULAJU_KP2027_PJ_T1_127_LESSON_V12_WORD_PDF_QA_20261122.zip"}
        for s,p in paths.items():
            with self.subTest(subject=s):
                data=(Path(root)/p).read_bytes()
                self.assertEqual(m.verify_qa_zip(s,data)["status"],m.RELEASE_STATUS)
                broken=data[:100]+b"X"+data[101:]
                with self.assertRaises(m.UnreleasedKP2027):m.verify_qa_zip(s,broken)

if __name__=="__main__":unittest.main()
