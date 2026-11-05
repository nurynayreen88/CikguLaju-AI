"""Tests stage-only 696-PDF preview bundle, including original real files when set."""
import hashlib,json,os,unittest,zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from preview_reader import PIPreviewBundleV5,PreviewBundleError

class PreviewTests(unittest.TestCase):
    def test_live_flag_is_rejected(self):
        with self.assertRaises(PermissionError):
            PIPreviewBundleV5('/tmp/not_there.zip')

    def create_synthetic_zip(self,path,*,bad_sha=False):
        count={2:112,3:147,4:151,5:143,6:143}
        records=[]
        with zipfile.ZipFile(path,'w') as z:
            for y,n in count.items():
                for l in range(1,n+1):
                    p=f'RPH_PRATONTON/Tahun_{y}/PI_T{y}_LESSON_{l:03d}_RPH_PRATONTON_STAGING.pdf'
                    data=f'%PDF-1.4\nDemo T{y} L{l}'.encode()
                    sha=hashlib.sha256(data).hexdigest()
                    if bad_sha and y==2 and l==35:sha='0'*64
                    records.append({'tahun':y,'lesson':l,'lesson_id':f'T{y}-L{l:03d}',
                        'pdf_path':p,'pdf_sha256':sha,'publish':'STAGING_ONLY','pages':1,'paper':'A4'})
                    z.writestr(p,data)
            z.writestr('KATALOG/preview_manifest.json',json.dumps({'status':'STAGING_ONLY_NOT_PUBLISHED','pdf_total':696}))
            z.writestr('KATALOG/preview_catalog.json',json.dumps(records))

    def test_synthetic_catalog_and_draft_guard(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'previews.zip';self.create_synthetic_zip(p)
            b=PIPreviewBundleV5(p,staging=True)
            with self.assertRaises(PermissionError):b.read_preview_pdf(2,35)
            self.assertTrue(b.read_preview_pdf(2,35,allow_teacher_draft=True).startswith(b'%PDF-'))
            self.assertEqual(b.get_record(6,143)['lesson_id'],'T6-L143')

    def test_sha_verification_fails_closed(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'bad.zip';self.create_synthetic_zip(p,bad_sha=True)
            b=PIPreviewBundleV5(p,staging=True)
            with self.assertRaises(PreviewBundleError):
                b.read_preview_pdf(2,35,allow_teacher_draft=True)

    def test_real_previews_optional(self):
        p=os.getenv('PI_V5_PREVIEW_ARCHIVE')
        if not p:self.skipTest('set PI_V5_PREVIEW_ARCHIVE for 696-PDF test')
        b=PIPreviewBundleV5(p,staging=True)
        for y,l in [(2,35),(3,65),(5,124),(6,141)]:
            self.assertTrue(b.read_preview_pdf(y,l,allow_teacher_draft=True).startswith(b'%PDF-'))

if __name__=='__main__':unittest.main()