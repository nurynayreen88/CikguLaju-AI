"""Owner-approved RPH layout contract. No educational text is generated here."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "web_v1_static_preview/Contoh_RPH_Semua_16.html"
CONTRACT = ROOT / "web/rph_login_canonical_layout_20261121.json"
SECTION = re.compile(r'<section id="rph-contoh-(\d+)" class="page (ltr|rtl)" style="--tone:(#[a-f0-9]+);--strong:(#[a-f0-9]+)"')


class TestOwnerApprovedRPHLayouts(unittest.TestCase):
    def test_all_sixteen_subject_examples_are_the_one_true_layout(self):
        content = GALLERY.read_text(encoding="utf-8")
        design = json.loads(CONTRACT.read_text(encoding="utf-8"))
        matches = list(SECTION.finditer(content))
        self.assertEqual(len(matches), 16)
        self.assertEqual(len(design["subjects"]), 16)
        for i, match in enumerate(matches):
            item = design["subjects"][i]
            section = content[match.start():matches[i + 1].start() if i < 15 else len(content)]
            self.assertEqual(item["id"], i + 1)
            self.assertEqual(item["direction"], match[2])
            self.assertEqual(item["tone"], match[3])
            self.assertEqual(item["strong"], match[4])
            self.assertEqual(item["hero_count"], section.count('<header class="hero"'))
            self.assertEqual(item["teacher_field_count"], section.count('class="teacher-row"'))
            self.assertEqual(item["main_table_count"], section.count('<table class="tbl"'))
            self.assertEqual(item["activity_title_count"], section.count('class="act-title"'))
            self.assertEqual(item["hero_count"], 1)
            self.assertEqual(item["teacher_field_count"], 4)
            self.assertEqual(item["main_table_count"], 2)
            self.assertEqual(item["activity_title_count"], 3)

    def test_jawi_arabic_are_rtl_not_a_separate_design(self):
        subjects = json.loads(CONTRACT.read_text(encoding="utf-8"))["subjects"]
        self.assertEqual({x["subject_code"] for x in subjects if x["direction"] == "rtl"}, {"PI", "ARAB"})
        self.assertEqual(sum(x["direction"] == "ltr" for x in subjects), 14)

    def test_content_must_remain_separate_from_template(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("not educational content", contract["rule"])
        self.assertEqual(contract["structure"]["hero"], 1)
        self.assertEqual(contract["structure"]["main_tables"], 2)


if __name__ == "__main__":
    unittest.main()
