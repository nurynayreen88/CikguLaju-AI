import unittest
from admin_usage_telegram import format_usage_summary, is_admin

class AdminUsageTelegramTests(unittest.TestCase):
    def test_exact_admin_id_only(self):
        self.assertTrue(is_admin(123, ['123', '456']))
        self.assertFalse(is_admin(12, ['123']))
        self.assertFalse(is_admin(None, ['123']))
        self.assertFalse(is_admin(123, []))

    def test_html_escaped_and_zero_stats(self):
        stats = dict(active_today=1, active_7d=2, active_30d=3,
                     rph_success=4, rph_failed=0,
                     top_subjects=[('<English & BM>', 4)])
        output = format_usage_summary(stats)
        self.assertIn('&lt;English &amp; BM&gt;', output)
        self.assertNotIn('<English & BM>', output)
        self.assertIn('RPH berjaya: <b>4</b>', output)

if __name__ == '__main__':
    unittest.main()
