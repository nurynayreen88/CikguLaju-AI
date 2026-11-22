"""Non-destructive source/provenance gate for KP2027 BM SJK Year 1.

This catalog is QA-only: do not treat 52 proposed PdP as a finalized RPT
and do not synthesize production RPH from an old KSSR template.
"""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'audits/kp2027_bm_sjk_year1_26sp_52pdp_20261122.json'
REGISTRY=ROOT/'audits/kp2027_year1_5dk_library_registry_20261122.json'
EXPECTED=("1.1.1","1.1.2","1.1.3","1.2.1","1.2.2","1.2.3","1.2.4",
          "2.1.1","2.1.2","2.1.3","2.2.1","2.2.2","2.3.1","2.3.2","2.3.3",
          "3.1.1","3.1.2","3.1.3","3.2.1","3.2.2","3.2.3",
          "4.1.1","4.1.2","4.1.3","4.2.1","4.2.2")

class BM_SJK_DocumentCatalog(unittest.TestCase):
    def test_26_sp_exact_dk_and_first_52_proposed_lessons(self):
        root=json.loads(CATALOG.read_text(encoding='utf-8'))
        self.assertEqual(root['source']['drive_file_id'],'19eJeNYAx5osXc2rvNjeE_pihg9euJS0S')
        self.assertEqual(root['source']['isbn'],'978-967-420-798-4')
        self.assertEqual(root['baseline_rpt']['drive_file_id'],'1gvpjsL-wy9py-ZU19Hv7OTFcvL6PwWha')
        self.assertEqual(root['counts']['unique_sp'],26)
        self.assertEqual(root['counts']['proposed_pdp'],52)
        records=root['records']
        self.assertEqual(tuple(rec['sp'] for rec in records),EXPECTED)
        self.assertEqual([n for rec in records for n in rec['rpt_pdp_proposals']],list(range(1,53)))
        for rec in records:
            self.assertEqual(rec['sk'],'.'.join(rec['sp'].split('.')[:2]))
            self.assertEqual(len(rec['rpt_pdp_proposals']),2)
            self.assertTrue(rec['focus'] and rec['bidang'] and rec['page_ref_pdf_draft'])
            self.assertEqual(rec['status'],'QA_ONLY_NOT_READY')
        self.assertEqual(root['counts']['ready_rph'],0)
        self.assertEqual(root['counts']['groups_published'],0)
        self.assertIn('BUKAN_RPT_TAHUNAN_FINAL',root['baseline_rpt']['status'])

    def test_only_five_verified_new_dk_documents_no_old_kssr(self):
        registry=json.loads(REGISTRY.read_text(encoding='utf-8'))
        found={x['code']:x for x in registry['sources']}
        self.assertEqual(set(found),{'BM_SK','BM_SJK','MATH','ALAM','PJ'})
        self.assertEqual(len({x['id'] for x in found.values()}),5)
        self.assertEqual(found['BM_SJK']['id'],'19eJeNYAx5osXc2rvNjeE_pihg9euJS0S')
        for source in found.values():
            self.assertEqual(source['status'],'DK_PRESENT')
        self.assertTrue(all('KSSR' not in str(x['code']) for x in registry['sources']))
        self.assertTrue(any('KSSR' in caution for caution in registry['cautions']))

if __name__=='__main__':
    unittest.main()
