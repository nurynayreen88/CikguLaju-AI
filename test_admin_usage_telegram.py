import unittest
from admin_usage_telegram import format_usage_summary, is_admin
from admin_usage_adapter import show_admin_usage

class AdminUsageTelegramTests(unittest.TestCase):
    def test_exact_admin_id_only(self):
        self.assertTrue(is_admin(123, ['123', '456']))
        self.assertFalse(is_admin(12, ['123']))
        self.assertFalse(is_admin(None, ['123']))
        self.assertFalse(is_admin(123, []))

    def test_non_admin_cannot_open_database(self):
        sent = []
        def forbidden_database():
            raise AssertionError('Unauthorized database access')
        allowed = show_admin_usage(
            42, lambda cid: False, forbidden_database,
            lambda cid, message, **kwargs: sent.append(message))
        self.assertFalse(allowed)
        self.assertIn('hanya untuk admin', sent[0])

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
