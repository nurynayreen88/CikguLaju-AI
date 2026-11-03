"""English RPH year value: rendered output only; production app is not imported."""
import re
import unittest
from pathlib import Path


def _display_value_from_app():
    """Execute the real, small display function without importing bot/DB modules."""
    source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    begin = source.index("def _rph_display_value(s,key,value):")
    end = source.index("\ndef _rph_title(s):", begin)
    fn_source = source[begin:end]
    context = {
        "re": re,
        "_is_english_subject": lambda state: str((state or {}).get("subject") or "").strip().casefold()
        in {"english", "bahasa inggeris"},
        "_rph_format_activity_lines": lambda value: value,
    }
    exec(compile(fn_source, "app.py:_rph_display_value", "exec"), context)
    return context["_rph_display_value"]


class EnglishRphYearDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.display_value = staticmethod(_display_value_from_app())

    def test_year_1_through_6_are_english_in_teacher_facing_output(self):
        for subject in ("English", "Bahasa Inggeris"):
            for year in range(1, 7):
                with self.subTest(subject=subject, year=year):
                    value = self.display_value(
                        {"subject": subject}, "TAHUN/TINGKATAN", f"Tahun {year}"
                    )
                    self.assertEqual(value, f"Year {year}")

    def test_existing_english_year_is_not_changed(self):
        self.assertEqual(
            self.display_value({"subject": "English"}, "TAHUN/TINGKATAN", "Year 4"),
            "Year 4",
        )

    def test_only_english_year_value_is_localized(self):
        for subject in ("Bahasa Melayu", "Matematik", "Sains", "Pendidikan Islam"):
            with self.subTest(subject=subject):
                self.assertEqual(
                    self.display_value({"subject": subject}, "TAHUN/TINGKATAN", "Tahun 2"),
                    "Tahun 2",
                )
        self.assertEqual(
            self.display_value({"subject": "English"}, "TAJUK", "Tahun 2"),
            "Tahun 2",
        )


if __name__ == "__main__":
    unittest.main()
