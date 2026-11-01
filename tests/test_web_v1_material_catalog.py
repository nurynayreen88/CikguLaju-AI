"""Unit tests for fail-closed Web V1 material visibility."""
import unittest
from web_v1_material_catalog import material_label, visible_materials


class MaterialCatalogTests(unittest.TestCase):
    def test_language_labels_follow_subject_and_file_language(self):
        self.assertEqual(material_label("workbook", "ENGLISH"), "Workbook / Activity Book")
        self.assertEqual(material_label("workbook", "BM"), "Buku Aktiviti")
        self.assertEqual(material_label("textbook", "MATH", "en"), "Student's Book / Textbook")
        self.assertEqual(material_label("textbook", "MATH", "bm"), "Buku Teks")
        self.assertEqual(material_label("audio", "ENGLISH"), "Lesson Audio")

    def test_only_verified_entitled_same_origin_materials_are_visible(self):
        items = [
            {"id": "a", "kind": "rph", "format": "pdf", "verified": True, "download_path": "/api/materials/download/a"},
            {"id": "b", "kind": "audio", "format": "mp3", "verified": True, "download_path": "/api/materials/download/b"},
            {"id": "c", "kind": "rph", "format": "pdf", "verified": False, "download_path": "/api/materials/download/c"},
            {"id": "d", "kind": "rph", "format": "pdf", "verified": True, "download_path": "https://evil.example/file"},
            {"id": "e", "kind": "rph", "format": "pdf", "verified": True, "download_path": "javascript:alert(1)"},
            {"id": "f", "kind": "rph", "format": "exe", "verified": True, "download_path": "/api/materials/download/f"},
        ]
        result = visible_materials(items, subject_code="ENGLISH", entitled_ids={"a", "c", "d", "e", "f"})
        self.assertEqual([x["id"] for x in result], ["a"])
        self.assertEqual(result[0]["label"], "Lesson Plan")

    def test_no_entitlements_no_downloads(self):
        self.assertEqual(visible_materials([{"id":"x", "kind":"rph", "format":"pdf", "verified":True, "download_path":"/api/materials/download/x"}], subject_code="BM", entitled_ids=set()), [])


if __name__ == "__main__":
    unittest.main()
