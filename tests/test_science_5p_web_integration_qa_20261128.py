import os
import unittest
from copy import deepcopy
from io import BytesIO
from unittest.mock import Mock, patch
from flask import Flask
from docx import Document
import fitz
from tools.audit_science_native_5p_documents_20261128 import inventory,support_inventory
from tools.science_5p_native_selection_preflight_20261128 import map_catalogue,verify_selection
from tools.science_5p_web_integration_qa_20261128 import create_test_blueprint,URL,ORIGIN,render_selected

def fixture(year, drafts):
    # Synthetic token values, but exact locked native-source lesson IDs/order.
    # This is NOT a verified production runtime catalogue.
    prefix={5:"v",6:"w"}[year]
    units={}
    records=[]
    for r in drafts:
        token=units.setdefault(r["unit"],prefix+format(len(units)+1,"024x"))
        records.append(dict(year=year,subject="SCIENCE",curriculum="KSSR",unit=token,
            unit_label=r["unit"],lesson_id=r["lesson_id"],lesson_label=r["title"],ready=False))
    return dict(year=year,source="telegram-native-pdp-sequence",catalogue_prefix=prefix,
                rpt_count_match=True,native_selection_count=len(records),unique_lesson_ids=len(records),
                unit_count=len(units),records=records)

class ScienceIntegrationQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drafts={y:inventory(y) for y in (5,6)}
        cls.rows={r["lesson_id"]:r for ds in cls.drafts.values() for r in ds}
        cls.support={k:v for y,ds in cls.drafts.items() for k,v in support_inventory(y,ds).items()}
        cls.catalogues={y:fixture(y,ds) for y,ds in cls.drafts.items()}
        cls.maps={y:map_catalogue(y,cls.catalogues[y],ds) for y,ds in cls.drafts.items()}

    def test_all_205_selections(self):
        self.assertEqual(sum(map(len,self.maps.values())),205)
        for year, mapping in self.maps.items():
            for cid,r in mapping.items():
                self.assertEqual(verify_selection(mapping,year,r["unit"],cid),r)
                with self.assertRaises(ValueError):
                    verify_selection(mapping,year,"u"+"a"*24,cid)
                with self.assertRaises(ValueError):
                    verify_selection(mapping,11-year,r["unit"],cid)
        for year in (5,6):
            for field,val in (("catalogue_prefix","u"),("rpt_count_match",False),("unique_lesson_ids",0)):
                bad=deepcopy(self.catalogues[year]);bad[field]=val
                with self.assertRaises(ValueError):map_catalogue(year,bad,self.drafts[year])
            bad=deepcopy(self.catalogues[year]);bad["records"][0],bad["records"][1]=bad["records"][1],bad["records"][0]
            with self.assertRaises(ValueError):map_catalogue(year,bad,self.drafts[year])
            bad=deepcopy(self.catalogues[year]);bad["records"][-1]["unit"]=bad["records"][0]["unit"]
            with self.assertRaises(ValueError):map_catalogue(year,bad,self.drafts[year])

    def setUp(self):
        self.account={"telegram_user_id":42,"authenticated":True,"free_remaining":10,"rakan_pembangun":False}
        self.uid=42
        self.debit=Mock(return_value={"ok":True,"remaining":9})
        self.renderer=Mock(wraps=render_selected)
        self.app=Flask(__name__);self.app.testing=True
        self.app.register_blueprint(create_test_blueprint(account_for_request=lambda req:(self.uid,self.account),
            mapping_for_year=lambda year:self.maps[year],rows=self.rows,support=self.support,
            debit=self.debit,renderer=self.renderer))
        self.client=self.app.test_client()
        cid=next(iter(self.maps[5]))
        self.payload={"year":5,"subject":"SCIENCE","unit":self.maps[5][cid]["unit"],"lesson":cid,"format":"word","rph_variant":"5p"}
    def post(self,**updates):
        return self.client.post(URL,json={**self.payload,**updates},headers={"Origin":ORIGIN})
    def test_access_and_quota(self):
        self.assertEqual(self.client.post(URL,json=self.payload).status_code,403)
        self.app.testing=False
        self.assertEqual(self.post().status_code,404)
        self.app.testing=True
        with patch.dict(os.environ,{"RENDER_SERVICE_ID":"srv-dbm5go8u01pc738f40cg"}):
            self.assertEqual(self.post().status_code,404)
        self.uid=None
        self.assertEqual(self.post().status_code,401)
        self.uid=42
        self.account["telegram_user_id"]=43
        self.assertEqual(self.post().status_code,403)
        self.account["telegram_user_id"]=42
        self.assertEqual(self.post(unit="u"+"a"*24).status_code,404)
        self.assertEqual(self.post(teacher_students="999").status_code,400)
        self.assertEqual(self.post(rph_variant="lengkap").status_code,404)
        self.assertEqual(self.post(reference="client-owned").status_code,400)
        self.renderer.side_effect=ValueError("render failed")
        self.assertEqual(self.post().status_code,503)
        self.renderer.side_effect=None
        self.debit.assert_not_called()
        out=self.post(teacher_class="5 Bestari",teacher_students="30")
        self.assertEqual(out.status_code,200)
        self.assertEqual(out.headers["X-RPH-Trial-Remaining"],"9")
        self.assertIn("5 Bestari",Document(BytesIO(out.data)).tables[0].cell(1,0).text)
        self.debit.assert_called_once()
        self.assertTrue(self.debit.call_args.args[3].startswith("web-rph:"))
        self.account["free_remaining"]=0
        self.assertEqual(self.post().status_code,403)
        self.debit.assert_called_once()
        self.account["free_remaining"]=1
        self.debit.return_value={"ok":False,"remaining":0}
        denied=self.post()
        self.assertEqual(denied.status_code,403)
        self.assertNotIn("Content-Disposition",denied.headers)
    def test_paid_personalized_pdf(self):
        self.account["rakan_pembangun"]=True
        self.account["free_remaining"]=0
        cid=next(iter(self.maps[6]))
        out=self.post(year=6,unit=self.maps[6][cid]["unit"],lesson=cid,format="pdf",
            teacher_class="6 Bestari",teacher_date="2027-03-02",teacher_start="08:00",
            teacher_end="08:30",teacher_students="30",reflection_mode="manual",
            reflection="Murid memerlukan bimbingan.")
        self.assertEqual(out.status_code,200)
        with fitz.open(stream=out.data,filetype="pdf") as d:
            self.assertEqual(len(d),1)
            txt=d[0].get_text()
            self.assertIn("6 Bestari",txt)
            self.assertIn("Murid memerlukan bimbingan.",txt)
        self.debit.assert_not_called()

if __name__=="__main__":
    unittest.main()
