"""KP2027 Year 1: logo, school and teacher on paid RPT Word/PDF only."""
from __future__ import annotations

import io
import struct
import unittest
import zlib
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from web import kp2027_year1_rpt_combined as bundles
from web import kp2027_year1_rpt_personalize as profile


def logo_png():
    def chunk(kind, content):
        return (struct.pack('>I', len(content)) + kind + content +
                struct.pack('>I', zlib.crc32(kind + content) & 0xffffffff))
    # Green 12x12 RGB icon, no external image fixtures / personal data.
    rows = b''.join(b'\x00' + b'\x22\x88\x55' * 12 for _ in range(12))
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', 12, 12, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


SCHOOL='SEKOLAH KEBANGSAAN AMAN DAMAI'
TEACHER='CIKGU SITI HAWA BINTI RAMLI'
IDENTITY={"school":SCHOOL,"teacher":TEACHER,"state":"Johor","logo":logo_png()}


class TestKP2027ProfileCover(unittest.TestCase):
    def test_free_rpt_exactly_same_original_word_pdf(self):
        for subject in bundles.SUBJECTS:
            for fmt in ('docx','pdf'):
                with self.subTest(subject=subject,fmt=fmt):
                    data,_,digest=bundles.document(subject,fmt)
                    result,applied=profile.for_download(
                        {"telegram_user_id":419,"rakan_pembangun":False},subject,fmt,data)
                    self.assertFalse(applied)
                    self.assertIs(data,result)
                    self.assertEqual(sha256(result).hexdigest(),digest)

    def test_paid_word_pdf_use_same_authoritative_profile(self):
        import fitz
        from docx import Document
        for subject in bundles.SUBJECTS:
            for fmt in ('docx','pdf'):
                with self.subTest(subject=subject,fmt=fmt):
                    data,_,_=bundles.document(subject,fmt)
                    with patch('web_v1_telegram_auth_routes._config',return_value={"account_backend":"supabase"}), \
                         patch('web.rpt_school_cover.school_identity',return_value=IDENTITY) as identity:
                        out,applied=profile.for_download(
                            {"telegram_user_id":419,"rakan_pembangun":True},subject,fmt,data)
                    self.assertTrue(applied)
                    self.assertNotEqual(data,out)
                    identity.assert_called_once_with({"account_backend":"supabase"},419,allow_teacher_only=True)
                    if fmt=='docx':
                        doc=Document(io.BytesIO(out))
                        self.assertEqual(doc.paragraphs[4].text,'NAMA SEKOLAH: '+SCHOOL)
                        self.assertEqual(doc.paragraphs[8].text,'NAMA GURU: '+TEACHER)
                        self.assertIn('Disediakan oleh: '+TEACHER,doc.paragraphs[10].text)
                        self.assertIn('NEGERI: Johor',doc.paragraphs[7].text)
                        self.assertEqual(doc.paragraphs[2].text,'RPT 2027')
                        self.assertEqual(len(doc.tables[0].columns),7)
                        with ZipFile(io.BytesIO(out)) as z:
                            self.assertTrue(any(x.startswith('word/media/image') for x in z.namelist()))
                        self.assertIn('Kumpulan A',doc.paragraphs[12].text)
                        self.assertIn('Kumpulan B',doc.paragraphs[3].text)
                    else:
                        original=fitz.open(stream=data,filetype='pdf')
                        updated=fitz.open(stream=out,filetype='pdf')
                        try:
                            self.assertEqual(len(original),len(updated))
                            first=updated[0].get_text()
                            self.assertIn(SCHOOL,first)
                            self.assertIn(TEACHER,first)
                            self.assertIn('Johor',first)
                            self.assertTrue(updated[0].get_images())
                            self.assertEqual(original[1].get_text(),updated[1].get_text())
                        finally:
                            original.close();updated.close()

    def test_paid_no_saved_identity_uses_generic_original(self):
        data,_,_=bundles.document('matematik','pdf')
        with patch('web_v1_telegram_auth_routes._config',return_value={"account_backend":"supabase"}), \
             patch('web.rpt_school_cover.school_identity',return_value=None):
            out,applied=profile.for_download(
                {"telegram_user_id":19,"rakan_pembangun":True},'matematik','pdf',data)
        self.assertIs(out,data)
        self.assertFalse(applied)

    def test_overlong_names_and_non_png_are_rejected(self):
        for field,bad in [('school','S'*161),('teacher','T'*101),('logo',b'not image')]:
            identity=dict(IDENTITY);identity[field]=bad
            with self.subTest(field=field),self.assertRaises(ValueError):
                profile._identity_fields(identity)

    def test_web_route_auth_gate_and_consistent_download_headers(self):
        server=(Path(__file__).resolve().parents[1]/'web/rpt_2027_all_http.py').read_text('utf-8')
        route=server.split('def download_kp2027_year1_gabungan(subject,fmt):',1)[1].split('@bp.get(',1)[0]
        self.assertIn('account,error=_account()',route)
        self.assertIn('paid_cover=_has_paid_access(account)',route)
        self.assertIn('personalize_rpt(account,subject,fmt,content)',route)
        self.assertIn('X-RPT-Personalization-Allowed',route)
        self.assertIn('X-RPT-Personalization-Applied',route)
        self.assertIn('X-RPT-Output-SHA256',route)
        self.assertIn('no-store, private',server)


if __name__=='__main__':
    unittest.main()
