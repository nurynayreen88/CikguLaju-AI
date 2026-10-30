import unittest
from rph_weekly_progress import summarize_jobs, retry_failed_only

class ProgressTests(unittest.TestCase):
    def test_summary(self):
        s=summarize_jobs(("a","b","c"),{"a":"succeeded","b":"failed"})
        self.assertEqual((s.succeeded,s.failed,s.pending),(1,1,1))
        self.assertEqual(s.retry_keys,("b",))
    def test_no_retry_success(self):
        self.assertEqual(retry_failed_only(("a",),{"a":"succeeded"}),())
    def test_duplicate(self):
        with self.assertRaises(ValueError): summarize_jobs(("a","a"),{})
    def test_invalid_status(self):
        with self.assertRaises(ValueError): summarize_jobs(("a",),{"a":"done"})
    def test_unexpected_key(self):
        with self.assertRaises(ValueError): summarize_jobs(("a",),{"b":"failed"})
if __name__=="__main__": unittest.main()
