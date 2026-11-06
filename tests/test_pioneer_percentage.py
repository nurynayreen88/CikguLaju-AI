import unittest
from pioneer_percentage import pioneer_percentage, pioneer_menu_line, pioneer_details

class PioneerPercentageTests(unittest.TestCase):
    def test_values(self):
        for count, expected in [(0,"0.0%"),(1,"0.5%"),(5,"2.5%"),(100,"50.0%"),(199,"99.5%"),(200,"100.0%"),(250,"100.0%"),(600,"100.0%"),(-1,"0.0%")]:
            self.assertEqual(pioneer_percentage(count), expected)
    def test_no_quota_exposed(self):
        for value in [pioneer_menu_line(1), pioneer_details(1)]:
            self.assertNotIn("/200", value)
            self.assertNotIn("199", value)
            self.assertNotIn("tempat", value.lower())

if __name__ == "__main__":
    unittest.main()
