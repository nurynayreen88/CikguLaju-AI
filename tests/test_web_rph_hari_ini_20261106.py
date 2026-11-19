"""RPH Hari Ini: shared timetable, strict authentication and native RPH-only handoff."""
from copy import deepcopy
from datetime import date
from contextlib import ExitStack
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from flask import Flask, jsonify
from web.rph_hari_ini_web import (
    assign_week_suggestions, bp, class_year, day_payload, subject_identity, week_payload,
    week_choices, weekly_catalog, weekly_rpt_suggestion,
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

    def test_week_expands_profile_and_skips_calendar_closures(self):
        rows = [{"day": day, "start": "08:00", "end": "09:00",
                 "class_name": "2 Amanah", "subject": "English"}
                for day in ("Ahad", "Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu")]
        schedule = {"entries": rows + [dict(rows[1], subject="Rehat")]}
        snapshot = deepcopy(schedule)
        target = date(2027, 2, 9)
        group_a = week_payload({"state_name": "Kedah"}, schedule, target, today=target)
        group_b = week_payload({"state_name": "W.P. Kuala Lumpur"}, schedule, target, today=target)
        self.assertEqual((group_a["group"], group_a["start"], group_a["end"], group_a["count"]),
                         ("A", "2027-02-07", "2027-02-13", 0))
        self.assertEqual((group_b["group"], group_b["start"], group_b["end"], group_b["count"]),
                         ("B", "2027-02-08", "2027-02-14", 0))
        target = date(2026, 11, 17)
        current = week_payload({"state_name": "Pahang"}, schedule, target, today=target)
        self.assertEqual((current["start"], current["end"], current["count"]),
                         ("2026-11-16", "2026-11-22", 5))
        self.assertEqual(current["days"][0]["entries"][0]["class_name"], "2 Amanah")
        self.assertIsNone(current["days"][0]["entries"][0]["rpt_suggestion"])
        self.assertEqual(snapshot, schedule)

    def test_week_choices_include_date_ranges_for_both_school_groups(self):
        today = date(2026, 11, 17)
        for group, first, last in (("A", "2026-11-15", "2026-11-21"),
                                   ("B", "2026-11-16", "2026-11-22")):
            with self.subTest(group=group):
                options = week_choices(today, group)
                self.assertEqual([row for row in options if row["current"]],
                                 [{"start": first, "end": last, "value": first, "current": True}])
                self.assertTrue(all(abs((date.fromisoformat(o["value"]) - today).days) <= 400
                                    for o in options))

    def test_holiday_closure_controls_both_daily_and_weekly_slots(self):
        cases = (
            (date(2026, 8, 31), "Pahang", "Cuti umum · Hari Kebangsaan", None),
            (date(2026, 11, 6), "Perak", "Cuti negeri · Hari Keputeraan Sultan Perak", "Pahang"),
            (date(2027, 7, 30), "Pahang", "Cuti negeri · Hari Keputeraan Sultan Pahang", "Selangor"),
            (date(2027, 2, 1), "W.P. Kuala Lumpur", "Cuti negeri · Hari Wilayah Persekutuan", "Pahang"),
            (date(2027, 8, 16), "Pahang", "Cuti ganti · Maulidur Rasul", "Kedah"),
            (date(2027, 10, 28), "Sarawak", "Cuti perayaan KPM · Deepavali", None),
        )
        for target, state, label, other_state in cases:
            with self.subTest(date=target, state=state):
                days = ("Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad")
                schedule = {"entries": [dict(EXAMPLE["entries"][0], day=days[target.weekday()])]}
                profile = {"state_name": state}
                daily = day_payload(profile, schedule, target, today=target)
                week = week_payload(profile, schedule, target, today=target)
                day = next(entry for entry in week["days"] if entry["date"] == target.isoformat())
                self.assertEqual(daily["closure"], label)
                self.assertTrue(daily["holiday_verified"])
                self.assertFalse(daily["entries"][0]["can_prepare"])
                self.assertIsNone(daily["entries"][0]["rpt_suggestion"])
                self.assertEqual(day["closure"], label)
                self.assertEqual(day["entries"], [])
                self.assertEqual(week["count"], 0)
                if other_state:
                    profile = {"state_name": other_state}
                    other = day_payload(profile, schedule, target, today=target)
                    self.assertEqual(other["closure"], "")
                    self.assertTrue(other["entries"][0]["can_prepare"])

    def test_holiday_confirmation_when_state_or_calendar_is_missing(self):
        cases = ((date(2027, 8, 31), "", "Isi negeri sekolah"),
                 (date(2028, 1, 3), "Pahang", "belum tersedia sepenuhnya"))
        for target, state, notice in cases:
            with self.subTest(date=target, state=state):
                daily = day_payload({"state_name": state}, EXAMPLE, target, today=target)
                weekly = week_payload({"state_name": state}, EXAMPLE, target, today=target)
                self.assertFalse(daily["holiday_verified"])
                self.assertEqual(daily["closure"], "")
                self.assertIn(notice, daily["holiday_notice"])
                self.assertIn(notice, weekly["holiday_notice"])

    def test_week_assigns_english_pairs_in_slot_order_for_each_class(self):
        rows = [{"day": day, "start": "08:00", "end": "09:00",
                 "class_name": name, "subject": "English"}
                for name in ("2 Amanah", "2 Bestari") for day in ("Isnin", "Rabu", "Jumaat")]
        target = date(2027, 1, 4)
        with patch("web.native_telegram_integrated_english_client.integrated_enabled", return_value=True):
            days = week_payload({"state_name": "Pahang"}, {"entries": rows}, target, today=target)["days"]
        for day in days:
            attach_progress(day, [])
        assign_week_suggestions(days)
        self.assertEqual([[s["suggested_session"] for s in d["entries"]] for d in days if d["entries"]],
                         [[[1], [1]], [[2, 3], [2, 3]], [[4], [4]]])

    def test_week_leaves_mismatched_progress_or_duration_for_teacher_selection(self):
        rows = [{"day": day, "start": "08:00", "end": "09:00",
                 "class_name": name, "subject": "English"}
                for name in ("2 Amanah", "2 Bestari") for day in ("Isnin", "Rabu", "Jumaat")]
        rows[-1]["end"] = "08:30"
        target = date(2027, 1, 11)
        with patch("web.native_telegram_integrated_english_client.integrated_enabled", return_value=True):
            days = week_payload({"state_name": "Pahang"}, {"entries": rows}, target, today=target)["days"]
        for day in days:
            attach_progress(day, [{"class_key": "2 amanah", "subject_code": "ENGLISH", "component": "",
                                   "pdp_date": "2027-01-08", "start_time": "08:00", "sequence_no": 2}])
        assign_week_suggestions(days)
        self.assertFalse(any(slot.get("suggested_session") for d in days for slot in d["entries"]))

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
        self.assertTrue(out["holiday_verified"])
        self.assertFalse(out["weekend"])
        self.assertEqual(data,original)

    def test_kedah_friday_is_weekend_even_if_old_schedule_has_rows(self):
        out=day_payload({"state_name":"Kedah"},EXAMPLE,date(2026,11,6),
                        today=date(2026,11,6))
        self.assertTrue(out["weekend"])
        self.assertEqual(out["closure"], "Hujung minggu")
        self.assertFalse(any(slot["can_prepare"] for slot in out["entries"]))
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

    def test_english_capacity_uses_same_class_and_excludes_the_state_holiday(self):
        english = dict(EXAMPLE["entries"][0], class_name="3 Cemerlang")
        schedule = {"entries": [
            dict(english, day="Isnin", start="08:00", end="09:00"),
            dict(english, day="Rabu", start="09:00", end="10:30", subject="BI"),
            dict(english, day="Jumaat", start="10:00", end="11:30"),
            dict(english, day="Khamis", class_name="3 Amanah"),
            dict(english, day="Khamis", subject="Sains"),
        ]}
        for state, minutes in [("Selangor", 150), ("Pahang", 240)]:
            with self.subTest(state=state):
                target = date(2027, 1, 18)
                result = day_payload({"state_name": state}, schedule, target, today=target)
                self.assertEqual(result["entries"][0]["rpt_capacity"], {
                    "scheduled_minutes": minutes, "required_minutes": 240,
                })
                self.assertEqual(result["entries"][0]["rpt_suggestion"]["lessons"], {
                    "": [8, 9, 10, 11],
                })
        holiday = date(2027, 1, 22)
        result = day_payload({"state_name": "Selangor"}, schedule, holiday, today=holiday)
        self.assertNotIn("rpt_capacity", result["entries"][0])

    @patch("web.native_telegram_integrated_english_client.integrated_enabled", return_value=True)
    def test_integrated_english_capacity_counts_one_hour_slot_per_open_day(self, _enabled):
        english = dict(EXAMPLE["entries"][0], class_name="3 Cemerlang")
        schedule = {"entries": [
            dict(english, day="Isnin", start="08:00", end="09:00"),
            dict(english, day="Isnin", start="10:00", end="11:00"),
            dict(english, day="Selasa", start="08:00", end="08:30"),
            dict(english, day="Rabu", start="08:00", end="08:30"),
            dict(english, day="Khamis", start="08:00", end="09:00", subject="BI"),
            dict(english, day="Jumaat", start="08:00", end="09:00"),
        ]}
        date_in_school = date(2027, 1, 18)
        for state, minutes in [("Selangor", 120), ("Pahang", 180)]:
            with self.subTest(state=state):
                day = day_payload({"state_name": state}, schedule, date_in_school, today=date_in_school)
                self.assertEqual(day["entries"][0]["rpt_capacity"], {
                    "scheduled_minutes": minutes, "required_minutes": 240,
                })

    def test_math_weekly_suggestions_follow_the_same_117_pdp_plan_as_telegram(self):
        short = {1, 5, 8, 10, 20, 30, 33, 35, 39}
        for year in (2, 3):
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

    def test_aligned_math_years_finish_in_week_38_with_the_audited_slot_lengths(self):
        for year, final_slots in ((4, [60, 30, 60, 30]), (5, [30, 60, 60, 30]),
                                  (6, [60, 30, 60, 30])):
            with self.subTest(year=year):
                weeks = weekly_catalog()[f"MATH:{year}"]
                self.assertEqual(set(map(int, weeks)), set(range(1, 39)) - {6, 18, 19})
                ordered = [weeks[str(n)] for n in sorted(map(int, weeks))]
                self.assertEqual([lesson for row in ordered for lesson in row[4][""]], list(range(1, 118)))
                lengths = [minutes for row in ordered for minutes in row[5]]
                self.assertEqual(sorted(lengths), [30] * 42 + [60] * 75)
                self.assertEqual(sum(lengths), 5760)
                self.assertEqual(
                    weekly_rpt_suggestion("Pahang", date(2027, 10, 19), "MATH", year),
                    {"week": 38, "group": "B", "lessons": {"": [114, 115, 116, 117]},
                     "slot_minutes": final_slots},
                )
                self.assertIsNone(weekly_rpt_suggestion("Pahang", date(2027, 10, 26), "MATH", year))

    def test_aligned_math_auto_assigns_only_when_the_timetable_matches_slot_lengths(self):
        schedule = {"entries": [
            {"day": day, "start": "08:00", "end": end, "class_name": "5 Bestari", "subject": "Matematik"}
            for day, end in (("Isnin", "08:30"), ("Selasa", "09:00"),
                             ("Rabu", "09:00"), ("Khamis", "08:30"))
        ]}
        target = date(2027, 10, 18)
        for last_end in ("08:30", "09:00"):
            schedule["entries"][-1]["end"] = last_end
            days = week_payload({"state_name": "Pahang"}, schedule, target, today=target)["days"]
            for day in days:
                attach_progress(day, [])
            assign_week_suggestions(days)
            self.assertEqual([s.get("suggested_session") for day in days for s in day["entries"]],
                             [[114], [115], [116], [117]] if last_end == "08:30" else [None] * 4)

    def test_pjpk_year3_suggests_two_pj_and_one_pk_before_assessment(self):
        expected = {"PJ": [37, 38], "PK": [32]}
        for state, group in (("Kedah", "A"), ("Johor", "B")):
            with self.subTest(state=state):
                self.assertEqual(
                    weekly_rpt_suggestion(state, date(2027, 10, 19), "PJPK", 3),
                    {"week": 38, "group": group, "lessons": expected},
                )
                for no_pdp in (date(2027, 5, 11), date(2027, 10, 26)):
                    self.assertIsNone(weekly_rpt_suggestion(state, no_pdp, "PJPK", 3))

    def test_science_year6_suggests_opening_unit_before_existing_lessons(self):
        weeks = weekly_catalog()["SCIENCE:6"]
        self.assertEqual(set(map(int, weeks)), set(range(1, 45)) - {6, 19})
        numbers = [number for row in weeks.values() for number in row[4][""]]
        self.assertEqual(numbers, [85, 86, 87, 88, 89, *range(1, 85)])
        self.assertEqual(
            weekly_rpt_suggestion("Pahang", date(2027, 1, 4), "SCIENCE", 6),
            {"week": 1, "group": "B", "lessons": {"": [85, 86]}},
        )
        self.assertEqual(len(weeks["39"][4][""]), 2)

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

    def test_sjk_and_dlp_timetable_use_only_their_own_catalogue(self):
        target = date(2027, 1, 11)
        profile = {"state_name": "Pahang"}
        subjects = [
            ("2 Amanah", "Sains"),
            ("2 Amanah", "Sains (DLP)"),
            ("2 Amanah", "Sains (SJKC)"),
            ("3 Amanah", "Matematik (SJKC)"),
            ("2 Amanah", "Bahasa Iban"),
        ]
        schedule = {"entries": [
            {"day": "Isnin", "start": f"{7+i:02d}:00", "end": f"{7+i:02d}:30",
             "class_name": cls, "subject": subject}
            for i, (cls, subject) in enumerate(subjects)
        ]}
        day = day_payload(profile, schedule, target, today=target)
        science, dlp, sjkc, math_sjkc, iban = day["entries"]
        self.assertTrue(science["can_prepare"])
        self.assertEqual(science["subject_code"], "SCIENCE")
        for row in (dlp, sjkc, math_sjkc, iban):
            self.assertFalse(row["can_prepare"])
            self.assertIsNone(row["subject_code"])
            self.assertIsNone(row["rpt_suggestion"])
        self.assertEqual(dlp["rpt_subject"], "science_dlp")
        self.assertEqual(dlp["rph_preview"], "SCIENCE_DLP")
        self.assertNotIn("rpt_subject", sjkc)
        self.assertIn("dalam penyediaan", sjkc["reason"])
        self.assertNotIn("rph_preview", sjkc)
        self.assertNotIn("rpt_subject", math_sjkc)
        self.assertIn("dalam penyediaan", iban["reason"])
        week = week_payload(profile, schedule, target, today=target)
        self.assertEqual(week["days"][0]["entries"], day["entries"])
        ready = day_payload(profile, schedule, target, today=target,
                            sjkc_catalogue=lambda year: year == 3)["entries"]
        self.assertEqual(ready[2], sjkc)
        self.assertTrue(ready[3]["can_prepare"])
        self.assertEqual(ready[3]["subject_code"], "MATH_SJKC")
        self.assertEqual(ready[3]["curriculum"], "sjkc")
        self.assertNotIn("rpt_subject", ready[3])


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

    def test_week_route_uses_the_authenticated_timetable_once(self):
        path = "/api/web/rph/minggu-ini"
        with self.app.app_context():
            unauthenticated = (jsonify({"error": "login"}), 401)
        with patch("web.rph_hari_ini_web._auth", return_value=(None, None, unauthenticated)):
            self.assertEqual(self.client.get(path).status_code, 401)
        with ExitStack() as stack:
            mocks = {name: stack.enter_context(patch("web.rph_hari_ini_web." + name, return_value=value))
                     for name, value in {"_auth": (self.conf, 123, None), "get_schedule": EXAMPLE,
                                         "get_profile": {"state_name": "Selangor"}, "read_progress": [],
                                         "malaysia_today": date(2026, 11, 6)}.items()}
            self.assertEqual(self.client.get(path + "?uid=456").status_code, 400)
            self.assertEqual(self.client.get(path + "?date=2026-11-06&date=2026-11-07").status_code, 400)
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        self.assertEqual(response.json["count"], 4)
        self.assertEqual(response.json["date"], "2026-11-06")
        self.assertEqual(response.json["start"], "2026-11-02")
        for name in ("get_profile", "get_schedule"):
            mocks[name].assert_called_once_with(self.conf["supabase_url"], self.conf["supabase_key"], 123)
        self.assertEqual({call.args[2] for call in mocks["read_progress"].call_args_list},
                         {"2026-11-05", "2026-11-06"})

    def test_daily_reuses_only_its_slot_suggestion_from_the_week(self):
        schedule = {"entries": [
            {"day": day, "start": "08:00", "end": "09:00",
             "class_name": "2 Amanah", "subject": "English"}
            for day in ("Isnin", "Rabu", "Jumaat")
        ]}
        target = "2027-01-06"
        with ExitStack() as stack:
            for name, value in {"_auth": (self.conf, 123, None), "get_schedule": schedule,
                                "get_profile": {"state_name": "Pahang"}, "read_progress": [],
                                "malaysia_today": date(2027, 1, 6)}.items():
                stack.enter_context(patch("web.rph_hari_ini_web." + name, return_value=value))
            stack.enter_context(patch("web.native_telegram_integrated_english_client.integrated_enabled",
                                      return_value=True))
            query = {"date": target}
            week = self.client.get("/api/web/rph/minggu-ini", query_string=query)
            today = self.client.get("/api/web/rph/hari-ini", query_string=query)
            self.assertEqual(week.status_code, 200)
            self.assertEqual(today.status_code, 200)
            week_day = next(day for day in week.json["days"] if day["date"] == target)
            self.assertEqual(today.json["entries"], week_day["entries"])
            self.assertEqual([slot["suggested_session"] for slot in today.json["entries"]], [[2, 3]])
            self.assertEqual([slot["suggested_session"] for day in week.json["days"]
                              for slot in day["entries"]], [[1], [2, 3], [4]])

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
        self.assertIn('if(button.dataset.webView==="today")window.rphTodayLoad?.();',page)
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
        self.assertIn('renderDaySlots(data,ticket,data.progress_editable)',daily)
        self.assertIn('choices.push(makeChoice(slot,choices.length,ticket,progressEditable,slots,day.date))',daily)
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
        self.assertIn('includedChoices().filter(c=>c.slot.can_prepare&&(!weekly||c.controls.lesson.value))',daily)
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
        self.assertIn('includedChoices().filter(c=>c.slot.can_prepare&&(!weekly||c.controls.lesson.value))',daily)
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
