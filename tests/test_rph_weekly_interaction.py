import unittest
from datetime import date
from rph_weekly_interaction import WeeklySelection, add_holiday, remove_holiday, toggle_cancelled_session, mark_previewed, confirm, require_ready

class InteractionTests(unittest.TestCase):
    def setUp(self):
        self.s=WeeklySelection("t",date(2026,10,26),date(2026,11,1))
    def test_confirmation(self):
        s=confirm(mark_previewed(self.s,"token"),"token")
        require_ready(s,"token")
    def test_edit_invalidates_confirmation(self):
        s=confirm(mark_previewed(self.s,"token"),"token")
        s=add_holiday(s,date(2026,10,27))
        with self.assertRaises(PermissionError): require_ready(s,"token")
    def test_cancel_invalidates(self):
        s=toggle_cancelled_session(confirm(mark_previewed(self.s,"x"),"x"),"session")
        self.assertIn("session",s.cancelled_session_ids)
        self.assertFalse(s.confirmed)
    def test_out_of_range(self):
        with self.assertRaises(ValueError): add_holiday(self.s,date(2026,11,2))
    def test_wrong_token(self):
        with self.assertRaises(ValueError): confirm(mark_previewed(self.s,"x"),"y")
    def test_remove_holiday(self):
        self.assertFalse(remove_holiday(add_holiday(self.s,date(2026,10,27)),date(2026,10,27)).holiday_dates)
if __name__=="__main__": unittest.main()
