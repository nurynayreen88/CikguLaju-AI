"""RPH Hari Ini: shared timetable, strict authentication and native RPH-only handoff."""
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from flask import Flask, jsonify
from web.rph_hari_ini_web import (
    bp, class_year, day_payload, subject_identity,
)

ROOT=Path(__file__).resolve().parents[1]
EXAMPLE={
    "entries":[
        {"day":"Jumaat","start":"10:30","end":"11:30","class_name":"3 Cemerlang","subject":"English"},
        {"day":"Jumaat","start":"07:30","end":"08:30","class_name":"4 Bestari","subject":"Bahasa Melayu"},
        {"day":"Khamis","start":"09:00","end":"10:00","class_name":"6 Amanah","subject":"Sains"},
        {"day":"Jumaat","start":"08:30","end":"09:30","class_name":"5 Amanah","subject":"Matematik"},
    ],"version":"2026-11-06T05:00:00Z",
}


class DailyTimetablePureTests(TestCase):
    def test_subject_aliases_fail_closed(self):
        for raw, expected in {
            "BM":("BM",None), " Bahasa Inggeris ":("ENGLISH",None),
            "Matematik":("MATH",None),"Sains":("SCIENCE",None),
            "Pendidikan Islam":("PI",None),"PJ":("PJPK","PJ"),
            "PK":("PJPK","PK"),"PJPK":("PJPK",None),
            "Bahasa Arab":("ARAB",None),"Pendidikan Muzik":("MUZIK",None),
            "RBT":("RBT",None),"Rehat":(None,None),
            "Perhimpunan":(None,None),
        }.items():
            with self.subTest(raw=raw):
                self.assertEqual(subject_identity(raw),expected)
        self.assertEqual(subject_identity("Cikgu Laju Algebra"),(None,None))

    def test_class_year_requires_leading_year(self):
        self.assertEqual(class_year("4 Bestari"),4)
        self.assertEqual(class_year("Tahun 6 Amanah"),6)
        self.assertEqual(class_year("T3 Cemerlang"),3)
        self.assertIsNone(class_year("Bestari 4"))
        self.assertIsNone(class_year("Tingkatan 4"))
        self.assertIsNone(class_year("10 Bestari"))

    def test_sorted_today_and_correct_timezone_independent_day(self):
        data=deepcopy(EXAMPLE)
        original=deepcopy(data)
        out=day_payload({"state_name":"Selangor"},data,date(2026,11,6),
                        today=date(2026,11,6))
        self.assertEqual([x["class_name"] for x in out["entries"]],
                         ["4 Bestari","5 Amanah","3 Cemerlang"])
        self.assertEqual([x["subject_code"] for x in out["entries"]],
                         ["BM","MATH","ENGLISH"])
        self.assertEqual(out["day"],"Jumaat")
        self.assertEqual(out["date"],"2026-11-06")
        self.assertEqual(out["count"],3)
        self.assertFalse(out["holiday_verified"])
        self.assertFalse(out["weekend"])
        self.assertEqual(data,original)

    def test_kedah_friday_is_weekend_even_if_old_schedule_has_rows(self):
        out=day_payload({"state_name":"Kedah"},EXAMPLE,date(2026,11,6),
                        today=date(2026,11,6))
        self.assertTrue(out["weekend"])
        self.assertIn("hujung minggu",out["holiday_notice"])
        self.assertEqual(out["count"],3) # no silent deletion

    def test_missing_schedule_is_empty_without_guessing(self):
        out=day_payload({"state_name":"Selangor"},{"entries":[]},
                        date(2026,11,6),today=date(2026,11,6))
        self.assertEqual(out["entries"],[])
        self.assertEqual(out["count"],0)

    def test_unmatched_year_or_subject_is_not_preparable(self):
        out=day_payload({"state_name":"Johor"},{"entries":[
            {"day":"Jumaat","start":"07:30","end":"08:00",
             "class_name":"Bestari","subject":"English"},
            {"day":"Jumaat","start":"08:00","end":"08:30",
             "class_name":"4 Amanah","subject":"Rehat"}]},
            date(2026,11,6),today=date(2026,11,6))
        self.assertTrue(all(not x["can_prepare"] for x in out["entries"]))


class DailyTimetableRouteTests(TestCase):
    def setUp(self):
        self.app=Flask(__name__)
        self.app.register_blueprint(bp)
        self.client=self.app.test_client()
        self.conf={"supabase_url":"https://example.supabase.co","supabase_key":"secret"}

    def test_authentication_required_before_reading_profile(self):
        with self.app.app_context():
            unauthenticated=(jsonify({"error":"login"}),401)
        with patch("web.rph_hari_ini_web._auth",
                   return_value=(None,None,unauthenticated)),patch(
                   "web.rph_hari_ini_web.get_schedule") as schedule:
            reply=self.client.get("/api/web/rph/hari-ini")
        self.assertEqual(reply.status_code,401)
        schedule.assert_not_called()

    def test_get_uses_authenticated_uid_shared_schedule_and_kl_date(self):
        with patch("web.rph_hari_ini_web._auth",return_value=(self.conf,123,None)),patch(
            "web.rph_hari_ini_web.malaysia_today",return_value=date(2026,11,6)),patch(
            "web.rph_hari_ini_web.get_profile",return_value={"state_name":"Selangor"}) as profile,patch(
            "web.rph_hari_ini_web.get_schedule",return_value=EXAMPLE) as schedule:
            reply=self.client.get("/api/web/rph/hari-ini")
        self.assertEqual(reply.status_code,200)
        self.assertEqual(reply.json["count"],3)
        self.assertEqual(reply.json["date"],"2026-11-06")
        profile.assert_called_once_with(self.conf["supabase_url"],self.conf["supabase_key"],123)
        schedule.assert_called_once_with(self.conf["supabase_url"],self.conf["supabase_key"],123)
        self.assertEqual(reply.headers["Cache-Control"],"no-store, private")

    def test_invalid_date_and_unknown_params_fail_closed(self):
        with patch("web.rph_hari_ini_web._auth",return_value=(self.conf,123,None)):
            for qs in ({"date":"2026-11-99"},{"date":"2026-11-06","uid":"999"},
                       {"date":"2026-11-06","page":"2"},{"date":"hello"}):
                with self.subTest(qs=qs):
                    self.assertEqual(self.client.get("/api/web/rph/hari-ini",
                                                      query_string=qs).status_code,400)

    def test_ui_routes_only_to_existing_native_selection_not_auto_generate(self):
        page=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf-8")
        daily=(ROOT/"web_v1_static_preview"/"rph-today.js").read_text("utf-8")
        launch=(ROOT/"tools"/"run_web_production.py").read_text("utf-8")
        self.assertIn('data-web-view="today"',page)
        self.assertIn('id="today-confirm-school-day"',page)
        self.assertIn("window.prepareRphFromToday",page)
        self.assertIn('showWebView("today");window.rphTodayLoad?.()',page)
        self.assertIn('subject.dispatchEvent(new Event("change"))',page)
        self.assertIn('"/api/web/rph/hari-ini"',daily)
        self.assertIn("!confirm.checked",daily)
        self.assertNotIn("generateRphFile(",daily)
        self.assertIn("app.register_blueprint(rph_hari_ini_bp)",launch)

    def test_all_daily_dropdowns_open_without_a_per_slot_button(self):
        page=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf-8")
        daily=(ROOT/"web_v1_static_preview"/"rph-today.js").read_text("utf-8")
        self.assertIn('id="today-generate-all" disabled>Jana Bahan Semua Lesson',page)
        self.assertIn('id="today-generate-status"',page)
        self.assertIn('choices.push(makeChoice(slot,i,ticket))',daily)
        self.assertIn('void initialize(c)',daily)
        self.assertIn('stage(c,name,label)',daily)
        self.assertIn('"/api/options?"',daily)
        self.assertIn('"bm-themes"',daily)
        self.assertIn('"bm-units"',daily)
        self.assertIn('"bm-topics"',daily)
        self.assertIn('"bm-pdp"',daily)
        self.assertIn('"components"',daily)
        self.assertIn('"units"',daily)
        self.assertIn('"pdp"',daily)
        self.assertIn('nativeLessonLabel(item,c.slot.subject_code)',daily)
        self.assertNotIn('prepareRphFromToday(',daily)
        self.assertNotIn('Pilih Tajuk / Lesson',daily)
        self.assertNotIn('daily-rph-prepare',daily)

    def test_one_jana_bahan_after_every_teachable_slot_selected(self):
        daily=(ROOT/"web_v1_static_preview"/"rph-today.js").read_text("utf-8")
        self.assertIn('selectable.some(c=>c.busy||!c.controls.lesson.value)',daily)
        self.assertIn('generateAll.disabled=loading||reviewing||!confirm.checked',daily)
        self.assertIn('generateAll.addEventListener("click",()=>{void generate();})',daily)
        self.assertIn('const selected=choices.filter(c=>c.slot.can_prepare)',daily)
        self.assertIn('await inspectOne(c,epoch)',daily)
        self.assertIn('const queue=selected.slice()',daily)
        self.assertIn('Math.min(3,queue.length)',daily)
        self.assertIn('c.resultList.replaceChildren()',daily)
        self.assertIn('window.refreshSharedRphBalance?.()',daily)
        self.assertIn('"/api/web/rph/availability?"',daily)
        self.assertIn('"/api/web/rph/extra-materials?"',daily)
        self.assertIn('"/api/web/rph/"+format+"?"',daily)
        self.assertNotIn('generateRphFile(',daily)
        self.assertNotIn('downloadRph(c,format,key,row.button);',daily.split('async function generate(){')[1])
        # The button discovers eligible assets only; Word/PDF quota is charged
        # by the original server route when its individual Download is clicked.
        self.assertIn('row.button.addEventListener("click",()=>{void downloadRph(',daily)

    def test_generated_material_cards_are_below_entire_subject_list(self):
        page=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf-8")
        daily=(ROOT/"web_v1_static_preview"/"rph-today.js").read_text("utf-8")
        # The output is a sibling following all subject selection cards and
        # the sole Jana Bahan button, not a child of an individual class card.
        self.assertLess(page.index('id="today-list"'),page.index('id="today-generate-all"'))
        self.assertLess(page.index('id="today-generate-all"'),page.index('id="today-results"'))
        self.assertLess(page.index('id="today-results"'),page.index('id="today-results-list"'))
        self.assertLess(page.index('id="today-results-list"'),page.index('class="daily-rph-footer"'))
        self.assertIn('aria-label="Bahan mengikut kelas dan subjek"',page)
        self.assertIn('id="today-results" class="daily-rph-output"',page)
        self.assertIn('id="today-results-list" class="daily-rph-result-list"',page)
        self.assertIn('resultsList.append(c.result)',daily)
        self.assertNotIn('card.append(c.result)',daily)
        self.assertNotIn('list.append(c.result)',daily)
        self.assertIn('resultsHost.hidden=false',daily)
        self.assertIn('resultsHost.scrollIntoView(',daily)
        self.assertIn('const selected=choices.filter(c=>c.slot.can_prepare)',daily)
        self.assertIn('const queue=selected.slice()',daily)
        # The same per-slot Download actions and source/quota path remain.
        self.assertIn('row.button.addEventListener("click",()=>{void downloadRph(',daily)
        self.assertIn('"/api/web/rph/"+format+"?"',daily)
        self.assertIn('"/api/web/rph/availability?"',daily)
        self.assertIn('"/api/web/rph/extra-materials?"',daily)

    def test_stale_or_changed_selections_clear_all_outputs(self):
        daily=(ROOT/"web_v1_static_preview"/"rph-today.js").read_text("utf-8")
        self.assertIn('function clearResults(){',daily)
        self.assertIn('resultsHost.hidden=true',daily)
        self.assertIn('resultsList.replaceChildren()',daily)
        self.assertIn('if(!c.result)continue;',daily)
        self.assertIn('const chosen=c.controls.lesson.selectedOptions[0]',daily)
        self.assertIn('c.resultSelection.textContent="Tahun "+c.slot.year',daily)
        self.assertIn('slot.class_name+" · "+slot.subject',daily)
        self.assertIn('create("span","daily-rph-time",slot.start+" – "+slot.end)',daily)
        self.assertIn('if(epoch!==batchEpoch||key!==selectedKey(c))return',daily)
        self.assertIn('if(!confirm.checked){reviewing=false;clearResults();}',daily)
        self.assertIn('batchEpoch++;',daily)
        self.assertIn('resultsHost.hidden=true;\n  resultsList.replaceChildren();\n  list.replaceChildren();',daily)

    def test_unavailable_materials_hidden_daily_and_manual(self):
        page=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf-8")
        daily=(ROOT/"web_v1_static_preview"/"rph-today.js").read_text("utf-8")
        self.assertNotIn('list.append(materialRow(placeholders[cat]))',page)
        self.assertNotIn('list.append(materialRow("Buku Teks"',page)
        self.assertNotIn('list.append(materialRow("Audio"',page)
        self.assertNotIn('list.append(materialRow("Buku Aktiviti"',page)
        self.assertIn('if(sourceConfirmed){',page)
        self.assertIn('if(verifiedRphFormats.includes("pdf"))',page)
        self.assertIn('if(verifiedRphFormats.includes("word"))',page)
        self.assertIn('if(!readyMaterialLink(item,c.slot.subject_code))continue;',daily)
        self.assertIn('if(!formats.includes(format))continue;',daily)
        self.assertIn('Tiada bahan yang disahkan tersedia',page)
        self.assertIn('Tiada bahan yang disahkan tersedia',daily)
        self.assertIn('if(!confirm.checked){reviewing=false;clearResults();}',daily)
        self.assertIn('reviewing=true;generateAll.disabled=true;updateAll()',daily)
        self.assertIn('if(epoch!==batchEpoch||key!==selectedKey(c))return',daily)


if __name__=="__main__":
    import unittest
    unittest.main()
