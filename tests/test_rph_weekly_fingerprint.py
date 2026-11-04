import unittest
from dataclasses import replace
from datetime import date
from rph_weekly_plan import Session
from rph_weekly_workflow import Confirmation
from rph_weekly_adapter import make_preview
from rph_weekly_fingerprint import preview_fingerprint, require_unchanged_preview

class FingerprintTests(unittest.TestCase):
    def setUp(self):
        self.c=Confirmation("t",date(2026,10,26),date(2026,11,1),confirmed=True)
        self.s=Session("a",date(2026,10,26),"1A","BM","L1")
    def snapshot(self, sessions=None, holidays=()):
        return make_preview(self.c,lambda *args:(self.s,) if sessions is None else sessions,lambda *args:holidays)
    def test_stable(self):
        self.assertEqual(preview_fingerprint(self.snapshot()),preview_fingerprint(self.snapshot()))
    def test_timetable_change(self):
        with self.assertRaises(ValueError):
            require_unchanged_preview(self.snapshot(),self.snapshot(sessions=(replace(self.s,lesson_id="L2"),)))
    def test_holiday_change(self):
        with self.assertRaises(ValueError):
            require_unchanged_preview(self.snapshot(),self.snapshot(holidays=(date(2026,10,26),)))
    def test_teacher_change(self):
        a=self.snapshot()
        b=replace(a,confirmation=replace(a.confirmation,teacher_id="other"))
        self.assertNotEqual(preview_fingerprint(a),preview_fingerprint(b))
if __name__=="__main__": unittest.main()
