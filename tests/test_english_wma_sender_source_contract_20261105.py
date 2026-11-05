"""Static contracts: preserve original WMA in English Y1/Y2 Telegram delivery.

No app import, media download, Telegram requests, user DB or format conversion.
Actual sent/audio contents and source-to-lesson mapping are separate checks.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def _function(name):
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    matches = [n for n in tree.body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == name]
    if not matches:
        raise AssertionError(f"Missing audio delivery function: {name}")
    return matches[-1]

def _constants(node):
    return [x.value for x in ast.walk(node) if isinstance(x, ast.Constant)
            and isinstance(x.value, str)]

def _file_upload_keys(node):
    names = set()
    for d in ast.walk(node):
        if isinstance(d, ast.Dict):
            for k in d.keys:
                if isinstance(k, ast.Constant) and k.value in ("document","audio"):
                    names.add(k.value)
    return names

class EnglishWmaSourcePreservation(unittest.TestCase):
    def test_y1_y2_sender_preserves_wma_name_and_mime(self):
        fn = _function("_eng12_send_verified_audio")
        words = _constants(fn)
        self.assertIn(".wma", words)
        self.assertIn("audio/x-ms-wma", words)
        self.assertIn("document", _file_upload_keys(fn))
        self.assertNotIn(".mp3", words)

    def test_generic_sender_is_not_a_verified_wma_path(self):
        fn = _function("_send_verified_media_rows_v2594")
        words = _constants(fn)
        self.assertIn(".mp3", words)
        self.assertIn("audio/mpeg", words)
        self.assertIn("audio", _file_upload_keys(fn))
        # Its current content type/extension is hard-wired to MP3.
        # Do NOT route WMA here or silently rename source WMA to .mp3.
        # Wrong-textbook Year4 WMA links are handled by the separate hold.
        self.assertNotIn("audio/x-ms-wma", words)

    def test_year4_wrong_book_24_wma_links_remain_quarantined_by_source(self):
        import json
        manifest = json.loads((ROOT / "audits/english_y4_wrong_book_audio_hold_manifest_20261105.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["route_count"],24)
        self.assertEqual(manifest["lesson_count"],19)
        self.assertTrue(all(x["file_name"].lower().endswith(".wma") for x in manifest["rows"]))
        self.assertEqual(manifest["observed_source_textbook"],"Super Minds 1")
        self.assertEqual(manifest["expected_textbook"],"Get Smart Plus 4")
        launcher = (ROOT / "tools/run_telegram_with_curriculum_api.py").read_text(encoding="utf-8")
        self.assertIn("install_y4_wrong_book_audio_hold(telegram_runtime)", launcher)

if __name__ == "__main__":
    unittest.main()
