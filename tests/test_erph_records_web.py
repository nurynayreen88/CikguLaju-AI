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

    def test_word_import_preview_no_store(self):
        from io import BytesIO
        from zipfile import ZipFile
        from xml.sax.saxutils import escape
        def cell(s):
            return '<w:tc><w:p><w:r><w:t>'+escape(s)+'</w:t></w:r></w:p></w:tc>'
        rows=[('Tajuk','Nombor'),('Standard Pembelajaran','1.1.1'),('Objektif','Murid menyebut nombor'),('Aktiviti PdP','Susun kad'),('Refleksi','')]
        xml='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:tbl>'+''.join('<w:tr>'+cell(a)+cell(b)+'</w:tr>' for a,b in rows)+'</w:tbl></w:body></w:document>'
        stream=BytesIO()
        with ZipFile(stream,'w') as z:z.writestr('word/document.xml',xml)
        raw=stream.getvalue()
        mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        with patch.object(m,'account',return_value=({},42,None)),patch.object(m,'store') as store:
            response=self.client.post('/api/erph/import-word',data=raw,content_type=mime,headers=ORIGIN)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json['fields']['standard_learning'],'1.1.1')
            self.assertIn('Susun kad',response.json['fields']['activities'])
            self.assertFalse(response.json['source_verified'])
            self.assertEqual(self.client.post('/api/erph/import-word',data=raw,content_type=mime).status_code,403)
            self.assertEqual(self.client.post('/api/erph/import-word',data=b'not a word file',content_type=mime,headers=ORIGIN).status_code,400)
            store.assert_not_called()

    def test_week_scope_is_sunday_to_saturday(self):
        with patch.object(m,'account',return_value=({},42,None)),patch.object(m,'store',return_value=[]) as store:
            r=self.client.get('/api/erph/records?date=2027-01-13&scope=week')
            self.assertEqual(r.status_code,200)
            self.assertEqual((r.json['start'],r.json['end']),('2027-01-10','2027-01-16'))
            self.assertEqual(store.call_args.args[1],42)
            self.assertEqual(store.call_args.args[3]['and'],'(teaching_date.gte.2027-01-10,teaching_date.lte.2027-01-16)')
    def test_preview_escapes_html_and_does_not_save(self):
        import json
        draft=dict(PAYLOAD,title='</script><script>alert(1)</script>',status='draft')
        with patch.object(m,'account',return_value=({},42,None)),patch.object(m,'store') as store:
            r=self.client.post('/erph/import-preview',data={'draft':json.dumps(draft)},headers=ORIGIN)
            self.assertEqual(r.status_code,200)
            self.assertNotIn(b'</script><script>alert(1)</script>',r.data)
            self.assertIn(b'\\u003c/script\\u003e',r.data)
            self.assertEqual(self.client.post('/erph/import-preview',data={'draft':json.dumps(draft)}).status_code,403)
            store.assert_not_called()

    def test_export_saved_records(self):
        from io import BytesIO
        from docx import Document
        import fitz
        with patch.object(m,'account',return_value=({},42,None)),patch.object(m,'store',return_value=[PAYLOAD,PAYLOAD]) as store:
            for fmt in ('word','pdf'):
                r=self.client.get('/api/erph/export?date=2027-01-11&scope=week&format='+fmt)
                self.assertEqual(r.status_code,200)
                self.assertIn('attachment',r.headers['Content-Disposition'])
                self.assertEqual(store.call_args.args[1],42)
                if fmt=='word':
                    text='\n'.join(p.text for p in Document(BytesIO(r.data)).paragraphs)
                else:
                    with fitz.open(stream=r.data,filetype='pdf') as doc:
                        self.assertEqual(len(doc),2)
                        text=' '.join(p.get_text() for p in doc)
                self.assertIn('Susun kad',text)
                self.assertIn('Refleksi',text)
                self.assertNotIn('Kumpulan A',text)
            self.assertEqual(self.client.get('/api/erph/export?date=2027-01-11&format=zip').status_code,400)
    def test_export_empty(self):
        with patch.object(m,'account',return_value=({},42,None)),patch.object(m,'store',return_value=[]):
            self.assertEqual(self.client.get('/api/erph/export?date=2027-01-11&format=pdf').status_code,404)

    def test_summary_year_and_leap_month(self):
        rows=[{'id':'00000000-0000-4000-8000-000000000001','teaching_date':'2028-02-29','status':'completed'},
              {'id':'00000000-0000-4000-8000-000000000002','teaching_date':'2028-02-29','status':'draft'}]
        for scope,n in [('year',12),('month',29)]:
            with patch.object(m,'account',return_value=({},42,None)),patch.object(m,'store',side_effect=[rows,[]]) as store:
                r=self.client.get('/api/erph/summary?date=2028-02-10&scope='+scope)
                self.assertEqual(r.status_code,200)
                self.assertEqual(len(r.json['items']),n)
                self.assertEqual(sum(x['total'] for x in r.json['items']),2)
                self.assertEqual(sum(x['completed'] for x in r.json['items']),1)
                self.assertEqual(store.call_args.args[1],42)
                self.assertTrue(store.call_args.kwargs['summary'])
                self.assertEqual(store.call_args.args[3]['id'],'gt.'+rows[-1]['id'])
    def test_summary_rejects_unknown_scope_or_owner(self):
        with patch.object(m,'account',return_value=({},42,None)),patch.object(m,'store') as store:
            for params in ('scope=week','scope=year&owner=99','scope=year&scope=month'):
                self.assertEqual(self.client.get('/api/erph/summary?date=2028-02-10&'+params).status_code,400)
            store.assert_not_called()

    def test_premium_and_merged_5p_word_import_preserves_fields(self):
        from io import BytesIO
        from docx import Document
        from web.erph_word_import import extract_docx
        def make(rows):
            d=Document();t=d.add_table(rows=0,cols=2)
            for a,b in rows:
                c=t.add_row().cells;c[0].text=a;c[1].text=b
            out=BytesIO();d.save(out);return out.getvalue()
        base=[('PENDIDIKAN JASMANI\nTahun 1\nTajuk: Asas pergerakan\nRPT Kumpulan A\nLesson 001','Maklumat PdP\nKelas:\nTarikh:'),
            ('Kandungan Pembelajaran','Asas pergerakan'),('Standard Pembelajaran','P1.1.1'),('Objektif Pembelajaran','Murid bergerak'),
            ('Kriteria Kejayaan','Dua percubaan'),('EMK / Nilai','Disiplin'),('PAK21 / KBAT','Komunikasi'),('Bahan / BBM','Kon'),
            ('Set Induksi','Pemanasan'),('Aktiviti Utama','Lompat'),('Pengukuhan / PBD','Pemerhatian'),('Penutup','Penyejukan'),
            ('Pemulihan','Bimbingan'),('Pengayaan','Cabaran'),('Refleksi (Auto / Manual)','Catatan')]
        fields=extract_docx(make(base))
        self.assertEqual(fields['title'],'Asas pergerakan')
        for v in ('Dua percubaan','Disiplin','Komunikasi','Kon','Pemanasan','Lompat','Pemerhatian','Penyejukan','Bimbingan','Cabaran'):
            self.assertIn(v,fields['activities'])
        self.assertEqual(fields['reflection'],'Catatan')
        phases=[('Aktiviti PdP (5P)','Penglibatan'),('','Lihat contoh'),('','Penerokaan'),('','Cuba gerak'),('','Penerangan'),('','Terangkan'),('','Pengembangan'),('','Ubah gerak'),('','Penilaian'),('','Semak gerak')]
        fields=extract_docx(make(base[:5]+phases+base[-3:]))
        for _,v in phases:self.assertIn(v,fields['activities'])
        with self.assertRaises(ValueError):
            extract_docx(make(base+[('Medan tidak dikenali','Kandungan penting')]))

    def test_editor_rejects_stale_import_and_save_callbacks(self):
        # Static regression contract; browser interaction QA is still required.
        with patch.object(m,'account',return_value=({},42,None)):
            html=self.client.get('/erph').get_data(as_text=True)
        self.assertIn('function edit(item){editorVersion++;',html)
        self.assertIn("'cancel').onclick=()=>{editorVersion++;form.hidden=true}",html)
        self.assertIn('if(version!==editorVersion||form.hidden)return;',html)
        self.assertIn('const version=editorVersion,recordId=editing;',html)
        self.assertIn("await api(recordId?'/'+encodeURIComponent(recordId):''",html)
        self.assertIn('if(version===editorVersion&&!form.hidden){day.value=',html)
