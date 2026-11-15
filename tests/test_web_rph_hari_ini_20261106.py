"""RPH Hari Ini: shared timetable, strict authentication and native RPH-only handoff."""
from copy import deepcopy
from datetime import date
from contextlib import ExitStack
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from flask import Flask, jsonify
from web.rph_hari_ini_web import (
    bp, class_year, day_payload, subject_identity, weekly_catalog, weekly_rpt_suggestion,
)

from web.rph_today_progress import attach_progress, lesson_signer, read_progress_summary
from web.teacher_profile_store import ProfileUnavailable

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

    def test_weekly_recommendations_use_published_subject_and_group_dates(self):
        entries = [
            dict(EXAMPLE["entries"][0], day="Ahad", class_name="2 Amanah"),
            dict(EXAMPLE["entries"][0], day="Isnin", class_name="1 Amanah"),
            dict(EXAMPLE["entries"][1], day="Isnin", class_name="2 Bestari",
                 subject="Pendidikan Jasmani"),
            dict(EXAMPLE["entries"][2], day="Isnin", class_name="2 Cemerlang",
                 subject="Sains"),
        ]
        schedule = {"entries": entries}
        sunday = date(2027, 1, 10)
        kedah = day_payload({"state_name": "KEDAH"}, schedule, sunday, today=sunday)
        self.assertEqual(kedah["entries"][0]["rpt_suggestion"], {
            "week": 2, "group": "A", "lessons": {"": [4, 5, 6, 7]},
        })
        johor = day_payload({"state_name": "Johor"}, schedule, sunday, today=sunday)
        self.assertIsNone(johor["entries"][0]["rpt_suggestion"])

        monday = date(2027, 1, 4)
        johor = day_payload({"state_name": "Johor"}, schedule, monday, today=monday)
        slots = {slot["subject_code"]: slot["rpt_suggestion"] for slot in johor["entries"]}
        self.assertIsNone(slots["ENGLISH"])  # No Year 1 mapping.
        self.assertEqual(slots["PJPK"], {
            "week": 1, "group": "B", "lessons": {"PJ": [1], "PK": [1]},
        })
        self.assertEqual(slots["SCIENCE"]["lessons"], {"": [1, 2]})

    def test_known_holidays_and_missing_state_do_not_suggest_lessons(self):
        entries = [dict(EXAMPLE["entries"][1], day="Isnin", class_name="2 Amanah",
                        subject="English")]
        for state, target in [("", date(2027, 1, 4)),
                              ("Selangor", date(2027, 3, 8)),
                              ("Kelantan", date(2027, 2, 8)),
                              ("Johor", date(2026, 11, 16))]:
            with self.subTest(state=state, target=target):
                output = day_payload({"state_name": state}, {"entries": entries},
                                     target, today=target)
                self.assertEqual(output["count"], 1)
                self.assertIsNone(output["entries"][0]["rpt_suggestion"])

    def test_english_weekly_capacity_and_holiday_dates(self):
        for year in range(2, 7):
            with self.subTest(year=year):
                self.assertEqual(weekly_rpt_suggestion("Terengganu", date(2027, 1, 4), "ENGLISH", year), {
                    "week": 1, "group": "A", "lessons": {"": [1, 2, 3]},
                })
                self.assertIsNone(weekly_rpt_suggestion("Kedah", date(2027, 2, 8), "ENGLISH", year))
                self.assertIsNone(weekly_rpt_suggestion("Johor", date(2027, 5, 19), "ENGLISH", year))
                self.assertEqual(len(weekly_rpt_suggestion("Johor", date(2027, 10, 25), "ENGLISH", year)["lessons"][""]), 2)
                self.assertEqual(weekly_rpt_suggestion("Johor", date(2027, 12, 3), "ENGLISH", year)["lessons"][""], [157, 158, 159, 160])

    def test_math_weekly_suggestions_follow_the_same_117_pdp_plan_as_telegram(self):
        short = {1, 5, 8, 10, 20, 30, 33, 35, 39}
        for year in range(2, 7):
            with self.subTest(year=year):
                weeks = weekly_catalog()[f"MATH:{year}"]
                self.assertEqual(set(map(int, weeks)), set(range(1, 45)) - {6, 19})
                sequence = []
                for n, data in sorted(weeks.items(), key=lambda item: int(item[0])):
                    lessons = data[4][""]
                    self.assertEqual(len(lessons), 2 if int(n) in short else 3)
                    sequence.extend(lessons)
                self.assertEqual(sequence, list(range(1, 118)))
                self.assertEqual(
                    weekly_rpt_suggestion("Pahang", date(2027, 1, 11), "MATH", year),
                    {"week": 2, "group": "B", "lessons": {"": [3, 4, 5]}},
                )

    def test_public_and_state_holidays_apply_to_other_subjects(self):
        for state, day in [("W.P. Kuala Lumpur", (2, 1)), ("Terengganu", (3, 4)),
                           ("Johor", (6, 8)), ("Selangor", (9, 16)), ("Sarawak", (10, 28))]:
            with self.subTest(state=state, day=day):
                self.assertIsNone(weekly_rpt_suggestion(state, date(2027, *day), "SCIENCE", 2))
        self.assertIsNotNone(weekly_rpt_suggestion("Johor", date(2027, 3, 4), "SCIENCE", 2))
        self.assertIsNotNone(weekly_rpt_suggestion("Sarawak", date(2027, 10, 27), "SCIENCE", 2))

    def test_every_published_kssr_rpt_omits_both_full_closure_weeks(self):
        for subject, weeks in weekly_catalog().items():
            with self.subTest(subject=subject):
                self.assertNotIn("6", weeks)
                self.assertNotIn("19", weeks)

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
        self.conf={"supabase_url":"https://example.supabase.co","supabase_key":"secret",
                   "CIKGULAJU_WEB_SESSION_SECRET":"test-session-secret"}

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
            "web.rph_hari_ini_web.get_schedule",return_value=EXAMPLE) as schedule,patch(
            "web.rph_hari_ini_web.read_progress",return_value=[]) as progress:
            reply=self.client.get("/api/web/rph/hari-ini")
        self.assertEqual(reply.status_code,200)
        self.assertEqual(reply.json["count"],3)
        self.assertEqual(reply.json["date"],"2026-11-06")
        self.assertTrue(reply.json["progress_editable"])
        progress.assert_called_once_with(self.conf,123,"2026-11-06")
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

    def test_completion_requires_owned_slot_current_date_and_signed_source_choice(self):
        signed = lesson_signer(self.conf).dumps([123, 3, "ENGLISH", "", 11])
        foreign = lesson_signer(self.conf).dumps([456, 3, "ENGLISH", "", 11])
        body = {"date": "2026-11-06", "start": "10:30", "class_name": "3 Cemerlang",
                "subject_code": "ENGLISH", "component": "", "token": signed}
        with ExitStack() as stack:
            for name, value in {"_auth": (self.conf, 123, None), "get_schedule": EXAMPLE,
                                "get_profile": {"state_name": "Selangor"}, "read_progress": [],
                                "malaysia_today": date(2026, 11, 6)}.items():
                stack.enter_context(patch("web.rph_hari_ini_web." + name, return_value=value))
            save = stack.enter_context(patch("web.rph_hari_ini_web.save_completion"))
            path = "/api/web/rph/hari-ini/completion"
            origin = {"Origin": "https://localhost"}
            for change in ({"token": foreign}, {"token": "invalid"}, {"start": "10:00"},
                           {"component": "PJ"}, {"date": "2026-11-13"}):
                with self.subTest(change=change):
                    self.assertEqual(self.client.post(path, json={**body, **change},
                                                      headers=origin).status_code, 400)
            self.assertEqual(self.client.post(path, json=body).status_code, 400)
            save.assert_not_called()
            self.assertEqual(self.client.post(path, json=body, headers=origin).status_code, 200)
            self.assertEqual(save.call_args.args[4:], ("", 11))
            self.assertEqual(self.client.post(path, json={**body, "token": None},
                                              headers=origin).status_code, 200)
            self.assertEqual(save.call_args.args[4:], ("", None))

    def test_profile_summary_is_private_and_lists_each_class_and_subject(self):
        path = "/api/web/rph/hari-ini/progress"
        scheduled = deepcopy(EXAMPLE)
        scheduled["entries"].append(dict(EXAMPLE["entries"][1], subject="PJPK"))
        summaries = {
            ("3 cemerlang", "ENGLISH", ""): {
                "completed": 2, "last_number": 4, "last_date": "2026-11-06",
            },
            ("2 setia", "MATH", ""): {
                "completed": 1, "last_number": 8, "last_date": "2026-10-29",
            },
        }
        with self.app.app_context():
            denied = (jsonify({"error": "login"}), 401)
        with patch("web.rph_hari_ini_web._auth", return_value=(None, None, denied)), patch(
                "web.rph_hari_ini_web.read_progress_summary") as read:
            self.assertEqual(self.client.get(path).status_code, 401)
            read.assert_not_called()
        today = date(2026, 11, 6)
        with patch("web.rph_hari_ini_web._auth", return_value=(self.conf, 123, None)), patch(
                "web.rph_hari_ini_web.malaysia_today", return_value=today), patch(
                "web.rph_hari_ini_web.get_schedule", return_value=scheduled), patch(
                "web.rph_hari_ini_web.read_progress_summary", return_value=summaries) as read:
            self.assertEqual(self.client.get(path, query_string={"uid": 456}).status_code, 400)
            reply = self.client.get(path)
            read.assert_called_once_with(self.conf, 123, today)
            read.side_effect = ProfileUnavailable("Test store is down")
            self.assertEqual(self.client.get(path).status_code, 503)
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(reply.headers["Cache-Control"], "no-store, private")
        self.assertEqual(reply.json["year"], 2026)
        rows = {(r["class_name"], r["subject"]): r for r in reply.json["entries"]}
        self.assertEqual(rows["3 Cemerlang", "Bahasa Inggeris"], {
            "class_name": "3 Cemerlang", "subject": "Bahasa Inggeris", "label": "Lesson",
            "completed": 2, "last_number": 4, "last_date": "2026-11-06",
        })
        self.assertEqual(rows["2 setia", "Matematik"]["completed"], 1)
        self.assertEqual(rows["4 Bestari", "Bahasa Melayu"]["completed"], 0)
        self.assertEqual(rows["4 Bestari", "Pendidikan Jasmani"]["completed"], 0)
        self.assertEqual(rows["4 Bestari", "Pendidikan Kesihatan"]["completed"], 0)

    def test_summary_counts_distinct_lessons_across_pages_by_class_and_component(self):
        def row(number, day, cls="3 cemerlang", component="PJ"):
            return {"class_key": cls, "subject_code": "PJPK", "component": component,
                    "pdp_date": day, "sequence_no": number}

        newest = row(4, "2026-11-06")
        with patch("web.rph_today_progress._request", side_effect=[
            [newest] * 500,
            [row(9, "2026-11-05"), row(4, "2026-11-03"),
             row(7, "2026-10-29", component="PK"), row(8, "2026-10-29", cls="3 amanah")],
        ]) as request:
            result = read_progress_summary(self.conf, 123, date(2026, 11, 6))
        self.assertEqual(result["3 cemerlang", "PJPK", "PJ"], {
            "completed": 2, "last_number": 4, "last_date": "2026-11-06",
        })
        self.assertEqual(result["3 cemerlang", "PJPK", "PK"]["completed"], 1)
        self.assertEqual(result["3 amanah", "PJPK", "PJ"]["last_number"], 8)
        for index, call in enumerate(request.call_args_list):
            filters = call.kwargs["filters"]
            self.assertEqual(filters["offset"], index * 500)
            self.assertEqual(filters["teacher_id"], "eq.123")
            self.assertEqual(filters["and"], "(pdp_date.gte.2026-01-01,pdp_date.lte.2026-11-06)")

    def test_progress_respects_slot_order_class_and_pjpk_component(self):
        def record(day, start, sequence, component="PJ", cls="3 cemerlang"):
            return {"pdp_date": day, "start_time": start + ":00", "sequence_no": sequence,
                    "subject_code": "PJPK", "class_key": cls, "component": component}

        slots = [dict(EXAMPLE["entries"][0], subject="PJPK", start=start, end=end)
                 for start, end in [("08:00", "08:30"), ("09:00", "09:30")]]
        target = date(2026, 11, 6)
        result = day_payload({}, {"entries": slots}, target, today=target)
        attach_progress(result, [record("2026-11-05", "08:00", 3),
                                 record("2026-11-06", "08:00", 4),
                                 record("2026-11-06", "09:00", 9, "PK"),
                                 record("2026-11-06", "08:00", 40, cls="3 amanah")])
        first, second = (row["progress"] for row in result["entries"])
        self.assertEqual(first, {"PJ": {"completed": 4, "previous": 3},
                                 "PK": {"completed": None, "previous": None}})
        self.assertEqual(second, {"PJ": {"completed": None, "previous": 4},
                                  "PK": {"completed": 9, "previous": None}})

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
        self.assertIn('choices.push(makeChoice(slot,i,ticket,data.progress_editable))',daily)
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
