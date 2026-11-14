"""Shared canonical class + timetable contract used by Telegram and Web."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from web import teacher_profile_store as store

STAMP="2026-11-05T07:00:00+00:00"
SLOT={"day":"Isnin","start":"07:30","end":"08:30","subject":"Matematik"}
SLOT2={"day":"Selasa","start":"09:00","end":"10:00","subject":"Sains"}


class MemoryRest:
    def __init__(self, profile=None, legacy=None):
        self.profile=deepcopy(profile)
        self.legacy=deepcopy(legacy)
        self.writes=[]
    def __call__(self, url, key, table, method, query, payload=None, opener=None):
        assert url=="https://test.supabase.co"
        assert key=="unit-test-only"
        assert query.get("telegram_user_id","eq.123")=="eq.123" or method=="POST"
        if method=="GET":
            return [deepcopy(self.profile if table=="teacher_profiles" else self.legacy)] if (
                self.profile if table=="teacher_profiles" else self.legacy) is not None else []
        assert table=="teacher_profiles", "Must not write into separate timetable table"
        if method=="PATCH":
            if query.get("updated_at")!="eq."+self.profile["updated_at"]:
                return []
            self.profile.update(deepcopy(payload))
            self.writes.append((table,method,deepcopy(payload)))
            return [deepcopy(self.profile)]
        if method=="POST":
            assert self.profile is None
            self.profile=deepcopy(payload)
            self.writes.append((table,method,deepcopy(payload)))
            return [deepcopy(self.profile)]
        raise AssertionError((table,method))


def profile():
    return {"telegram_user_id":123,"display_name":"Cikgu A",
            "school_name":"SK Ilmu", "state_name":"W.P. Kuala Lumpur",
            "class_names":["4 Bestari","5 Amanah"],
            "class_profiles":[
                {"name":"4 Bestari","students":33,
                 "timetable":[deepcopy(SLOT)],"custom_marker":"must-survive"},
                {"name":"5 Amanah","students":29,"timetable":[]},
            ],"updated_at":STAMP}


class SharedStorageTests(unittest.TestCase):
    def setUp(self):
        self.memory=MemoryRest(profile())
        self.mock=patch.object(store,"_rest",side_effect=self.memory)
        self.mock.start();self.addCleanup(self.mock.stop)

    def test_web_read_telegram_schedule_and_student_counts(self):
        data=store.get_profile("https://test.supabase.co","unit-test-only",123)
        self.assertEqual(data["state_name"],"W.P. Kuala Lumpur")
        self.assertEqual(data["class_names"],["4 Bestari","5 Amanah"])
        schedule=store.get_schedule("https://test.supabase.co","unit-test-only",123)
        self.assertEqual(schedule["entries"],[{**SLOT,"class_name":"4 Bestari"}])
        self.assertEqual(schedule["version"],data["version"])
        self.assertEqual(self.memory.writes,[])

    def test_web_profile_save_preserves_telegram_student_and_schedule(self):
        args={"display_name":"Cikgu B","school_name":"SK Bahagia","state_name":"Johor",
              "class_names":["4 Bestari","5 Amanah","6 Ceria"],"version":STAMP}
        version=store.save_profile("https://test.supabase.co","unit-test-only",123,args)
        self.assertNotEqual(version,STAMP)
        rows=self.memory.profile["class_profiles"]
        self.assertEqual([x["name"] for x in rows],args["class_names"])
        self.assertEqual(rows[0]["students"],33)
        self.assertEqual(rows[0]["custom_marker"],"must-survive")
        self.assertEqual(rows[0]["timetable"],[SLOT])
        self.assertEqual(rows[1]["students"],29)
        self.assertEqual(rows[2]["timetable"],[])
        self.assertEqual(self.memory.profile["class_names"],args["class_names"])
        self.assertEqual(self.memory.profile["school_name"],"SK BAHAGIA")
        self.assertEqual(self.memory.profile["display_name"],"CIKGU B")
        self.assertEqual(len(self.memory.writes),1)
        self.assertNotIn("teacher_timetables",[x[0] for x in self.memory.writes])

    def test_web_timetable_edit_immediately_visible_to_telegram_class_records(self):
        payload={"entries":[{**SLOT2,"class_name":"5 Amanah"}],"version":STAMP}
        ver=store.save_schedule("https://test.supabase.co","unit-test-only",123,payload)
        self.assertNotEqual(ver,STAMP)
        rows=self.memory.profile["class_profiles"]
        self.assertEqual(rows[0]["timetable"],[])
        self.assertEqual(rows[0]["students"],33)
        self.assertEqual(rows[1]["timetable"],[SLOT2])
        self.assertEqual(rows[1]["students"],29)
        self.assertEqual(store.get_schedule("https://test.supabase.co","unit-test-only",123)["entries"],
                         [{**SLOT2,"class_name":"5 Amanah"}])
        self.assertEqual(len(self.memory.writes),1)
        self.assertEqual(self.memory.writes[0][0],"teacher_profiles")

    def test_guided_import_writes_aliases_classes_and_selected_slots_together(self):
        args = {"changes": [{"entry": {**SLOT2, "class_name": "6 Ceria", "subject": "MT"},
                             "replace": None}], "version": STAMP,
                "subject_aliases": {"MT": "Matematik"}, "class_aliases": {"6C": "6 Ceria"}}
        version = store.save_schedule("https://test.supabase.co", "unit-test-only", 123, args, guided=True)
        self.assertEqual(len(self.memory.writes), 1)
        self.assertEqual(self.memory.profile["timetable_subject_aliases"], {"MT": "Matematik"})
        self.assertEqual(self.memory.profile["timetable_class_aliases"], {"6C": "6 Ceria"})
        classes = self.memory.profile["class_profiles"]
        self.assertEqual(classes[0], profile()["class_profiles"][0])
        self.assertEqual(classes[2]["timetable"], [{**SLOT2, "subject": "Matematik"}])
        with self.assertRaises(store.ProfileConflict):
            store.save_schedule("https://test.supabase.co", "unit-test-only", 123, args, guided=True)
        args["version"] = version
        args["changes"][0]["replace"] = {**SLOT, "class_name": "4 Bestari"}
        args["changes"][0]["entry"] = {**SLOT, "class_name": "6 Ceria", "subject": "Sains"}
        store.save_schedule("https://test.supabase.co", "unit-test-only", 123, args, guided=True)
        self.assertEqual(self.memory.profile["class_profiles"][0]["timetable"], [])
        self.assertEqual(len(self.memory.profile["class_profiles"][2]["timetable"]), 2)

    def test_telegram_edits_then_web_reloads_actual_current_data(self):
        self.memory.profile["display_name"]="Cikgu Telegram"
        self.memory.profile["class_profiles"][0]["timetable"].append(SLOT2)
        self.memory.profile["updated_at"]="2026-11-05T08:00:00+00:00"
        self.assertEqual(store.get_profile("https://test.supabase.co","unit-test-only",123)["display_name"],
                         "Cikgu Telegram")
        timetable=store.get_schedule("https://test.supabase.co","unit-test-only",123)
        self.assertEqual(len(timetable["entries"]),2)
        self.assertEqual(timetable["version"],self.memory.profile["updated_at"])

    def test_reject_removing_class_with_saved_timetable(self):
        args={"display_name":"Cikgu A","school_name":"SK Ilmu",
              "state_name":"Johor","class_names":["5 Amanah"],"version":STAMP}
        with self.assertRaises(store.ProfileValidation):
            store.save_profile("https://test.supabase.co","unit-test-only",123,args)
        self.assertEqual(self.memory.writes,[])
        self.assertEqual(len(self.memory.profile["class_profiles"]),2)

    def test_stale_browser_does_not_clobber_telegram_change(self):
        args={"display_name":"Cikgu B","school_name":"SK Ilmu",
              "state_name":"Johor","class_names":["4 Bestari","5 Amanah"],
              "version":STAMP}
        self.memory.profile["updated_at"]="2026-11-05T10:00:00+00:00"
        with self.assertRaises(store.ProfileConflict):
            store.save_profile("https://test.supabase.co","unit-test-only",123,args)
        with self.assertRaises(store.ProfileConflict):
            store.save_schedule("https://test.supabase.co","unit-test-only",123,
                                {"entries":[],"version":STAMP})
        self.assertEqual(self.memory.writes,[])

    def test_old_web_timetable_is_read_only_fallback_until_migration(self):
        self.memory.profile["class_profiles"]=[]
        self.memory.legacy={"telegram_user_id":123,"entries":[{**SLOT,"class_name":"4 Bestari"}],
                            "updated_at":STAMP}
        t=store.get_schedule("https://test.supabase.co","unit-test-only",123)
        self.assertEqual(len(t["entries"]),1)
        self.assertEqual(t["version"],STAMP)
        self.assertEqual(self.memory.writes,[])
        # An explicitly cleared current Telegram timetable never falls back.
        self.memory.profile["class_profiles"]=[
            {"name":"4 Bestari","students":None,"timetable":[]},
            {"name":"5 Amanah","students":None,"timetable":[]}]
        self.assertEqual(store.get_schedule("https://test.supabase.co","unit-test-only",123)["entries"],[])

    def test_profile_and_schedule_share_one_updated_at_version(self):
        version=store.save_profile("https://test.supabase.co","unit-test-only",123,
                                   {"display_name":"Cikgu A","school_name":"SK Ilmu",
                                    "state_name":"Johor","class_names":["4 Bestari","5 Amanah"],
                                    "version":STAMP})
        next_version=store.save_schedule("https://test.supabase.co","unit-test-only",123,
                                         {"entries":[{**SLOT,"class_name":"4 Bestari"}],
                                          "version":version})
        self.assertEqual(self.memory.profile["updated_at"],next_version)
        self.assertEqual(len(self.memory.writes),2)


class PublicCopyTests(unittest.TestCase):
    def test_no_database_location_announced_to_teacher(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]/"web_v1_static_preview"
        html=(root/"index.html").read_text("utf8")
        js=(root/"teacher-profile.js").read_text("utf8")
        self.assertNotIn("Supabase",html)
        self.assertNotIn("Supabase",js)
        self.assertIn('id="profile-refresh"',html)
        self.assertIn("refreshTeacherProfile",js)
        self.assertIn("teacherProfileState.timetableVersion=result.version;",js)
        self.assertIn("teacherProfileState.profileVersion=result.version;",js)
        self.assertIn("W.P. Kuala Lumpur",html)
        self.assertIn("Telegram",html)


if __name__=="__main__":
    unittest.main()
