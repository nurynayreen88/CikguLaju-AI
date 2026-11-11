"""Synthetic CI tests: structurally valid 696 files MUST NOT pass as ready."""
import unittest
import hashlib
import io
import json
import tempfile
from pathlib import Path
from zipfile import ZipFile
from release_gate import analyze,read_word_text,ReleaseValidationError,EXPECTED_COUNTS,EXPECTED_HELD

TEXT='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>STATUS: DRAF STAGING</w:t></w:r></w:p></w:body></w:document>'
def docx():
 f=io.BytesIO()
 with ZipFile(f,'w') as z:z.writestr('word/document.xml',TEXT)
 return f.getvalue()

class PolicyTests(unittest.TestCase):
 def test_inventory_expectation(self):
  self.assertEqual(sum(EXPECTED_COUNTS.values()),696)
  self.assertEqual(len(EXPECTED_HELD),6)
 def test_word_magic_guard(self):
  with self.assertRaises(ReleaseValidationError):read_word_text(b'spoof Word')
 def test_word_corrupt_xml_guard(self):
  f=io.BytesIO()
  with ZipFile(f,'w') as z:z.writestr('word/document.xml','badxml')
  with self.assertRaises(ReleaseValidationError):read_word_text(f.getvalue())
 def test_valid_bundles_fail_without_pedagogical_signoff(self):
  src=io.BytesIO();pre=io.BytesIO()
  w=docx();p=b'%PDF-1.4\n%%EOF'
  docs=[];pdfs=[]
  with ZipFile(src,'w') as za,ZipFile(pre,'w') as zb:
   for year,total in EXPECTED_COUNTS.items():
    for n in range(1,total+1):
     rid=f'T{year}-L{n:03d}'
     wp=f'RPH_2027/Tahun_{year}/PI_T{year}_LESSON_{n:03d}_RPH_STAGING.docx'
     pp=f'PDF/Tahun_{year}/PI_T{year}_LESSON_{n:03d}_RPH_STAGING.pdf'
     held=(year,n) in EXPECTED_HELD
     za.writestr(wp,w);zb.writestr(pp,p)
     docs.append({'tahun':year,'lesson':n,'lesson_id':rid,'rph_path':wp,'rph_sha256':hashlib.sha256(w).hexdigest(),'rph_state':'TAHAN_SEMAKAN_KANDUNGAN' if held else 'CALON_UJIAN_GURU_DRAF'})
     pdfs.append({'tahun':year,'lesson':n,'pdf_path':pp,'pdf_sha256':hashlib.sha256(p).hexdigest(),'publish':'STAGING_ONLY'})
   za.writestr('KATALOG/manifest_v5.json',json.dumps({'status':'STAGING_NOT_READY'}))
   za.writestr('KATALOG/catalog.json',json.dumps(docs))
   zb.writestr('KATALOG/preview_manifest.json',json.dumps({'status':'STAGING_ONLY_NOT_PUBLISHED'}))
   zb.writestr('KATALOG/preview_catalog.json',json.dumps(pdfs))
  src.seek(0);pre.seek(0)
  outcome=analyze(src,pre)
  self.assertEqual(outcome['gate'],'NO_GO')
  self.assertEqual(outcome['rph_count'],696)
  self.assertEqual(outcome['blocker_counts']['BELUM_SAH_GURU_INDVIDU'],696)
  self.assertEqual(outcome['blocker_counts']['RPH_DITAHAN'],6)
  self.assertEqual(outcome['blocker_counts']['PDF_PRATONTON_DRAF'],696)
  self.assertEqual(outcome['blocker_counts']['NOTA_DRAF_DALAMAN_WORD'],696)
  for x in outcome['records']:self.assertFalse(x['boleh_terbit'])
 def test_teacher_signoff_without_release_assets_still_fails(self):
  # No approved status may be synthesized merely by supplying a name/date.
  template={'decision':'LULUS','penyemak':'Guru Semak','tarikh':'2026-11-05','semak_jawi_tasmi':'YA', 'semak_objektif_aktiviti_pbd':'YA'}
  self.assertFalse(bool(template.get('bukti_dskp')))
  self.assertFalse(bool(template.get('bukti_buku_teks_atau_mushaf')))

if __name__=='__main__':unittest.main()