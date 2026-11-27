import os
import unittest
from unittest.mock import patch
from flask import Flask
from web import erph_records_web as m

PAYLOAD=dict(teaching_date='2027-01-11',class_name='1 Bestari',subject_name='Matematik',
 start_time='08:00',end_time='09:00',title='Nombor',standard_content='Nombor bulat',standard_learning='Menyebut nombor',objectives='Menyebut nombor',
 activities='Susun kad nombor',reflection='',rph_format='5p',status='saved')
ORIGIN={'Origin':m.ORIGIN}
class ErphTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__);app.register_blueprint(m.bp)
        self.client=app.test_client()
    def test_flag_off(self):
        with patch.dict(os.environ,{m.FLAG:'0'}):
            self.assertEqual(self.client.get('/api/erph/records?date=2027-01-11').status_code,404)
    def test_owner_spoof_and_wrong_origin(self):
        with patch.object(m,'account',return_value=({},42,None)),patch.object(m,'store') as store:
            self.assertEqual(self.client.post('/api/erph/records',json=PAYLOAD).status_code,403)
            self.assertEqual(self.client.post('/api/erph/records',json=dict(PAYLOAD,owner_telegram_id=99),headers=ORIGIN).status_code,400)
            store.assert_not_called()
    def test_owner_derived_from_session(self):
        with patch.object(m,'account',return_value=({},42,None)),patch.object(m,'store',return_value=[{'id':'x'}]) as store:
            self.assertEqual(self.client.post('/api/erph/records',json=PAYLOAD,headers=ORIGIN).status_code,201)
            self.assertEqual(store.call_args.args[4]['owner_telegram_id'],42)
    def test_other_owner_cannot_update(self):
        with patch.object(m,'account',return_value=({},42,None)),patch.object(m,'store',return_value=[]) as store:
            rid='00000000-0000-4000-8000-000000000001'
            self.assertEqual(self.client.put('/api/erph/records/'+rid,json=PAYLOAD,headers=ORIGIN).status_code,404)
            self.assertEqual(store.call_args.args[1],42)
            self.assertEqual(store.call_args.args[3],{'id':'eq.'+rid})
    def test_validation(self):
        for changes in ({'end_time':'07:00'},{'teaching_date':'2027-02-30'},{'status':'completed'},{'activities':''}):
            with self.assertRaises(ValueError):m.validate(dict(PAYLOAD,**changes))
        self.assertEqual(m.validate(PAYLOAD),PAYLOAD)
    def test_store_always_filters_owner(self):
        from urllib.parse import parse_qs,urlsplit
        with patch.object(m,'_settings',return_value=('https://example.test','key')),patch.object(m,'_headers',return_value={}),patch.object(m,'build_opener') as opener:
            response=opener.return_value.open.return_value.__enter__.return_value
            response.read.return_value=b'[]'
            m.store({},42,'PATCH',{'id':'eq.test','owner_telegram_id':'eq.99'},PAYLOAD)
            req=opener.return_value.open.call_args.args[0]
            self.assertEqual(parse_qs(urlsplit(req.full_url).query)['owner_telegram_id'],['eq.42'])

    def test_menu_availability_requires_verified_account(self):
        with patch.dict(os.environ,{m.FLAG:'0'}):
            self.assertEqual(self.client.get('/api/erph/availability').status_code,404)
        with patch.object(m,'account',return_value=({},42,None)):
            self.assertEqual(self.client.get('/api/erph/availability').json,{'enabled':True})
    def test_page_contains_existing_timetable_endpoint_and_safe_editor(self):
        with patch.object(m,'account',return_value=({},42,None)):
            r=self.client.get('/erph')
            self.assertEqual(r.status_code,200)
            self.assertIn(b'/api/web/rph/hari-ini?date=',r.data)
            self.assertIn(b'if(j.closure)',r.data)
            self.assertIn(b'name="standard_learning"',r.data)
            self.assertIn(b'private, no-store',r.headers['Cache-Control'].encode())
