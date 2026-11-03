"""Synthetic tests of read-only Matematik T4 crosswalk guard."""
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from tools.check_matematik_t4_crosswalk import check

class CrosswalkSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        ids=[f'{i:02d}' for i in range(1,82) if i!=11]+['11A','11B','11C']
        self.records=[]
        self.zip=self.root/'rph.zip'
        with zipfile.ZipFile(self.zip,'w') as z:
            for i,identity in enumerate(ids):
                data=f'word{identity}'.encode()
                z.writestr(f'83_RPH_Word/RPH_T4_{identity}_PRA_READY.docx',data)
                self.records.append({'rph_id':identity,'sha256_docx':hashlib.sha256(data).hexdigest(),
                   'rpt2027_block':i%42+1,'runtime_approved':False,'source_status':'PRA-READY'})
        self.manifest=self.root/'manifest.json'
        self.save()

    def save(self):
        self.manifest.write_text(json.dumps({'rph':self.records,'release_allowed':False}))

    def test_matching_package_still_not_deployable(self):
        result=check(self.zip,self.manifest)
        self.assertTrue(result['integrity_ok'])
        self.assertFalse(result['release_allowed'])

    def test_changed_file_is_rejected(self):
        self.records[0]['sha256_docx']='0'*64
        self.save()
        self.assertFalse(check(self.zip,self.manifest)['integrity_ok'])

    def test_ready_mark_rejected(self):
        self.records[0]['runtime_approved']=True
        self.save()
        self.assertFalse(check(self.zip,self.manifest)['integrity_ok'])

    def test_missing_block_rejected(self):
        for r in self.records:
            if r['rpt2027_block']==42:r['rpt2027_block']=41
        self.save()
        self.assertFalse(check(self.zip,self.manifest)['integrity_ok'])

    def test_missing_rph_rejected(self):
        self.records.pop()
        self.save()
        self.assertFalse(check(self.zip,self.manifest)['integrity_ok'])

if __name__=='__main__':unittest.main()