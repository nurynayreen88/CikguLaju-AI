import unittest
from datetime import date
from rph_weekly_plan import Session
from rph_weekly_workflow import Confirmation
from rph_weekly_adapter import week_bounds, make_preview, confirmed_manifest

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.start=date(2026,10,26)
        self.end=date(2026,11,1)
        self.c=Confirmation("t",self.start,self.end,confirmed=True)
        self.sessions=(Session("s1",self.start,"1A","BM","L1"),)
    def test_week_bounds(self):
        self.assertEqual(week_bounds(date(2026,10,30),0),(self.start,self.end))
        self.assertEqual(week_bounds(date(2026,10,30),6),(date(2026,10,25),date(2026,10,31)))
    def test_preview_and_manifest(self):
        p=make_preview(self.c,lambda teacher,start,end:self.sessions,lambda start,end:())
        self.assertEqual(p.included_count,1)
        self.assertEqual(len(confirmed_manifest(p,self.c)),1)
    def test_stale_confirmation_rejected(self):
        p=make_preview(self.c,lambda *args:self.sessions,lambda *args:())
        with self.assertRaises(ValueError):
            confirmed_manifest(p,Confirmation("t",self.start,self.end,confirmed=False))
    def test_holiday(self):
        p=make_preview(self.c,lambda *args:self.sessions,lambda *args:(self.start,))
        self.assertEqual(p.included_count,0)
        self.assertEqual(len(confirmed_manifest(p,self.c)),0)
if __name__=="__main__": unittest.main()
