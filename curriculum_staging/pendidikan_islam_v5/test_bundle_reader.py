"""Pendidikan Islam V5 staging reader verification (no production writes)."""
import hashlib
import json
import os
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from bundle_reader import PIBundleV5, BundleValidationError

class PIBundleReaderTest(unittest.TestCase):
    def test_live_mode_is_blocked(self):
        with self.assertRaises(PermissionError):
            PIBundleV5('/tmp/nonexistent.zip')

    def make_fixture(self, out, *, missing_guide=False, bad_sha=False):
        records=[]
        for year, count in [(2,112),(3,147),(4,151),(5,143),(6,143)]:
            for lesson in range(1,count+1):
                docx=f'RPH_2027/CALON_UJIAN_GURU_DRAF/Tahun_{year}/PI_T{year}_LESSON_{lesson:03d}_RPH_STAGING.docx'
                data=b'PK\x03\x04'+f'fake T{year} L{lesson}'.encode()
                record={'tahun':year,'lesson':lesson,'lesson_id':f'T{year}-L{lesson:03d}',
                        'rph_path':docx,'rph_sha256':hashlib.sha256(data).hexdigest(),
                        'optional_tasmi_guide':None,'optional_guide_is_official':False}
                records.append((record,data))
        exceptions={(2,35),(3,145),(5,141),(6,14),(6,18),(6,26),(6,137),(6,141)}
        with zipfile.ZipFile(out,'w') as z:
            for rec,data in records:
                if bad_sha and rec['tahun']==2 and rec['lesson']==35:
                    rec['rph_sha256']='f'*64
                z.writestr(rec['rph_path'],data)
                if (rec['tahun'],rec['lesson']) in exceptions:
                    name=f"PANDUAN_TASMI/T{rec['tahun']}_L{rec['lesson']:03d}.pdf"
                    rec['optional_tasmi_guide']=name
                    if not (missing_guide and rec['tahun']==2 and rec['lesson']==35):
                        z.writestr(name,b'%PDF-1.4\nsynthetic fixture')
            z.writestr('KATALOG/catalog.json',json.dumps([x for x,_ in records]))
            z.writestr('KATALOG/manifest_v5.json',json.dumps({'status':'STAGING_NOT_READY','publication_status':'DRAF','rph_count':696}))

    def test_synthetic_696_lessons_and_eight_guides(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'pi.zip';self.make_fixture(p)
            bundle=PIBundleV5(p,staging=True)
            self.assertEqual(len(bundle.lesson_ids()),696)
            self.assertEqual(sum(bool(bundle.record(*x)['optional_tasmi_guide']) for x in bundle.lesson_ids()),8)
            with self.assertRaises(PermissionError):
                bundle.read_rph(2,35)
            self.assertTrue(bundle.read_rph(2,35,allow_teacher_draft=True).startswith(b'PK'))
            self.assertTrue(bundle.read_optional_tasmi_guide(2,35).startswith(b'%PDF-'))
            self.assertIsNone(bundle.read_optional_tasmi_guide(2,1))

    def test_fail_closed_on_missing_guide(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'missing.zip';self.make_fixture(p,missing_guide=True)
            with self.assertRaises(BundleValidationError):
                PIBundleV5(p,staging=True)

    def test_fail_closed_on_rph_checksum_mismatch(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'checksum.zip';self.make_fixture(p,bad_sha=True)
            b=PIBundleV5(p,staging=True)
            with self.assertRaises(BundleValidationError):
                b.read_rph(2,35,allow_teacher_draft=True)

    def test_integration_bundle_optional(self):
        archive=os.environ.get('PI_V5_ARCHIVE')
        if not archive:
            self.skipTest('Set PI_V5_ARCHIVE to run full real bundle test')
        bundle=PIBundleV5(archive,staging=True)
        self.assertEqual(len(bundle.lesson_ids()),696)
        self.assertEqual(sum(1 for key in bundle.lesson_ids() if bundle.record(*key)['optional_tasmi_guide'] is not None),8)
        self.assertTrue(bundle.read_rph(2,35,allow_teacher_draft=True).startswith(b'PK'))
        self.assertEqual(bundle.record(6,141)['source_exception'],'4_surah_juz30_julat_cadangan')

if __name__ == '__main__':
    unittest.main()