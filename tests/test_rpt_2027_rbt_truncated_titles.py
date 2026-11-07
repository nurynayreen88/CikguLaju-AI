"""RPT RBT PDF-only text recovery without mutating original source records."""
from __future__ import annotations
import re
import unittest

from rpt_2027.common.rbt_truncated_title_guard_staging import (
    EXPECTED_INCOMPLETE, expand_rbt_display_titles,
)
from rpt_2027.rbt.pdf_runtime import source_rows
from scripts.build_rpt_2027_standard_preview import rbt_records


class RBTTruncatedTitleQA(unittest.TestCase):
    def test_exact_12_truncated_titles_are_recovered_from_dskp(self):
        self.assertEqual(sum(len(x) for x in EXPECTED_INCOMPLETE.values()), 12)
        for year, expected in EXPECTED_INCOMPLETE.items():
            with self.subTest(year=year):
                raw = source_rows(year)
                rows = rbt_records(year)
                self.assertEqual(len(rows), 32)
                self.assertEqual(len(raw), 32)
                actual = {int(row["id"]) for row in rows if row.get("source_topic")}
                self.assertEqual(actual, expected)
                for idx, (s, r) in enumerate(zip(raw, rows), 1):
                    self.assertEqual(r["id"], f"{idx:03d}")
                    self.assertEqual(r["sk"], s["SK"])
                    self.assertEqual(r["sp"], s["SP"])
                    self.assertFalse(r["week"])
                    self.assertFalse(r["a_start"])
                    self.assertFalse(r["b_start"])
                    source_topic = re.sub(
                        rf"^PdP\s+0*{idx}\s*[:：—–-]\s*", "",
                        s["Tajuk PdP"], flags=re.IGNORECASE
                    )
                    if idx in expected:
                        self.assertEqual(r["source_topic"], source_topic)
                        self.assertEqual(r["topic_display_status"],
                                         "FULL_DSKP_SP_EXACT_STAGING_ONLY")
                        official = r["sp_display"].splitlines()[0].split(" — ", 1)[1]
                        self.assertEqual(r["topic"], official)
                        self.assertNotEqual(r["topic"], source_topic)
                        self.assertEqual(len(s["Tajuk PdP"]), 99)
                    else:
                        self.assertNotIn("source_topic", r)
                        self.assertEqual(r["topic"], source_topic)

    def test_fail_closed_on_modified_source_order(self):
        rows = rbt_records(4)
        raw = source_rows(4)
        raw[0]["PdP"] = "27"
        with self.assertRaises(ValueError):
            expand_rbt_display_titles(4, raw, rows)


if __name__ == "__main__":
    unittest.main()
