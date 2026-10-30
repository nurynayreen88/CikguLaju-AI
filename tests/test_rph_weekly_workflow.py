import unittest
from datetime import date
from rph_weekly_plan import Session
from rph_weekly_workflow import Confirmation, preview, approved_sessions, generation_key, manifest

D=date(2026,10,26)
S=(Session("a",D,"1A","BM","L1"),Session("b",date(2026,10,27),"1A","BM","L2"),Session("c",date(2026,10,28),"1B","BI","L3"))
class WeeklyTests(unittest.TestCase):
    def confirm(self, **kw):
        return Confirmation("teacher",D,date(2026,11,1),**kw)
    def test_no_leave(self):
        p=preview(S,frozenset(),self.confirm())
        self.assertEqual(len(p.included),3)
        with self.assertRaises(PermissionError): approved_sessions(p,self.confirm())
        self.assertEqual(len(approved_sessions(p,self.confirm(confirmed=True))),3)
    def test_official_and_extra(self):
        p=preview(S,frozenset({D}),self.confirm(extra_holidays=frozenset({date(2026,10,27)})))
        self.assertEqual([s.session_id for s in p.included],["c"])
    def test_cancel_single_class(self):
        p=preview(S,frozenset(),self.confirm(cancelled_sessions=frozenset({"c"})))
        self.assertEqual(len(p.excluded),1)
    def test_duplicate_prevented(self):
        p=preview(S+(S[0],),frozenset(),self.confirm(confirmed=True))
        self.assertEqual(p.duplicates,("a",))
        with self.assertRaises(ValueError): approved_sessions(p,self.confirm(confirmed=True))
    def test_key_stable(self):
        self.assertEqual(generation_key("teacher",S[0]),generation_key("teacher",S[0]))
        self.assertNotEqual(generation_key("teacher",S[0]),generation_key("other",S[0]))
    def test_manifest(self):
        self.assertEqual(len(manifest(preview(S,frozenset(),self.confirm()),"teacher")),3)
    def test_outside_week_rejected(self):
        with self.assertRaises(ValueError): preview(S,frozenset(),self.confirm(extra_holidays=frozenset({date(2026,11,2)})))
if __name__=="__main__": unittest.main()
