"""Read-only regression of actual legacy Telegram Year 4 Student Book mapping.

Extracts Python AST from the large app.py without importing/executing the bot,
starting Telegram, fetching books or consuming any user credits.
"""
import ast
from pathlib import Path
import re
import unittest


APP = Path(__file__).resolve().parents[1] / "app.py"
SOURCE = APP.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(APP))


def _literal(name):
    for node in TREE.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("Missing source data " + name)


def _function(name, env, *, occurrence=0):
    nodes = [node for node in TREE.body
             if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(nodes) > occurrence, "Missing function " + name
    module = ast.fix_missing_locations(ast.Module(body=[nodes[occurrence]], type_ignores=[]))
    local = dict(env)
    exec(compile(module, str(APP), "exec"), local)
    return local[name]


class EnglishY4LegacyPageParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = _literal("_Y4_SB_PAGES_V25230")
        cls.overrides = _literal("_EN34_MAIN_SB_V25231")
        cls.parser = _function(
            "_en4_verified_page_tokens_v20261112", {"_re_v25232": re}
        )

        def resolver(row, year):
            lesson = int(row["lesson_no"])
            if year == 4:
                return cls.overrides.get((year, lesson), cls.pages.get(lesson, ""))
            return "15-16" if year == 3 else ""

        cls.base_pages = _function("_en_book_pages_v25232", {
            "_english_primary_year_number_v2517": lambda raw: int(str(raw).split()[-1]),
            "_en34_verified_sb_pages_v25230": resolver,
            "_en4_verified_page_tokens_v20261112": cls.parser,
            "_v25232_nums": _function("_v25232_nums", {"_re_v25232": re}),
            "_lesson_activity_book_rows_v2407": lambda ss: [],
            "_en3_book_refs_v2595": lambda r: {},
        }, occurrence=0)

    def _state(self, lesson, year=4, **extra):
        return {"year": "Tahun " + str(year), "subject": "English",
                "_en98_selected_staging_row": {"lesson_no": str(lesson)},
                **extra}

    def test_three_sow_conflicts_fixed_at_legacy_source(self):
        self.assertEqual(self.pages[43], "121")
        self.assertEqual(self.pages[103], "73")
        self.assertEqual(self.pages[157], "110–111")
        self.assertEqual(self.overrides[(4, 157)], "110–111")
        for lesson, expected in ((43, [121]), (103, [73]),
                                 (157, [110, 111])):
            with self.subTest(lesson=lesson):
                self.assertEqual(self.base_pages(self._state(lesson), "textbook"),
                                 expected)

    def test_legacy_parser_reads_all_81_verified_main_pages(self):
        self.assertEqual(len(self.pages), 81)
        for lesson in self.pages:
            with self.subTest(lesson=lesson):
                rows = self.base_pages(self._state(lesson), "textbook")
                self.assertGreaterEqual(len(rows), 1)
                self.assertLessEqual(len(rows), 4)
                self.assertEqual(rows, list(range(rows[0], rows[-1] + 1)))
                self.assertTrue(all(1 <= page <= 177 for page in rows))

    def test_comma_list_no_longer_discards_second_page(self):
        self.assertEqual(self.base_pages(self._state(18), "textbook"), [15, 16])
        self.assertEqual(self.base_pages(self._state(11), "textbook"), [12, 13])
        self.assertEqual(self.base_pages(self._state(54), "textbook"), [38, 39])

    def test_unknown_or_bad_y4_source_fails_closed_no_stale_fallback(self):
        for value in ("", "15, 17", "73, 73", "110–133",
                      "27, 28, 29, 30, 31", "15, 16; 17",
                      "0", "178", "15, 16 and 17", "15–19"):
            with self.subTest(value=value):
                self.assertEqual(self.parser(value), [])
        missing = {"year": "Tahun 4", "subject": "English",
                   "lesson_no": 43, "textbook_page_start": 27,
                   "textbook_page_end": 31}
        self.assertEqual(self.base_pages(missing, "textbook"), [])
        unknown = self._state(99, textbook_page_start=27, textbook_page_end=31)
        self.assertEqual(self.base_pages(unknown, "textbook"), [])

    def test_other_years_keep_legacy_routing(self):
        self.assertEqual(self.base_pages(self._state(18, year=3), "textbook"),
                         [15, 16])
        self.assertEqual(self.base_pages({
            "year": "Tahun 2", "subject": "English",
            "textbook_page_start": 20, "textbook_page_end": 21
        }, "textbook"), [20, 21])


if __name__ == "__main__":
    unittest.main()
