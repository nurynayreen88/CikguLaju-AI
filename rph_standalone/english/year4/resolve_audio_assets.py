"""Read-only Year 4 lesson audio resolver for QA/staging.

Usage:
    python rph_standalone/english/year4/resolve_audio_assets.py 097
No network calls, Telegram calls, or production database access.
Only lessons independently verified in the mapping file are resolved.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def resolve_lesson_audio(lesson):
    if isinstance(lesson, bool):
        raise ValueError("Lesson must be an integer from 1 to 160")
    if isinstance(lesson, int):
        number = lesson
    elif isinstance(lesson, str) and lesson.isascii() and lesson.isdecimal():
        number = int(lesson)
    else:
        raise ValueError("Lesson must be an integer from 1 to 160")
    if not 1 <= number <= 160:
        raise ValueError("Lesson must be between 1 and 160")
    assets = json.loads((HERE / "QA_CLASS_CD_ASSET_MANIFEST_20261031.json").read_text(encoding="utf-8"))
    mapping = json.loads((HERE / "QA_VERIFIED_LESSON_AUDIO_MAPPING_20261031.json").read_text(encoding="utf-8"))
    if assets.get("year") != 4 or mapping.get("year") != 4:
        raise ValueError("Incorrect source year")
    if mapping.get("asset_manifest") != "QA_CLASS_CD_ASSET_MANIFEST_20261031.json":
        raise ValueError("Audio mapping points to an unexpected manifest")
    lesson_key = f"{number:03d}"
    if lesson_key not in mapping["lessons"]:
        return []  # Not yet verified; never infer a track.
    page = mapping.get("teacher_book_page_by_lesson", {}).get(lesson_key)
    if not isinstance(page, int) or isinstance(page, bool) or page <= 0:
        raise ValueError(f"Missing Teacher Book provenance for Lesson {lesson_key}")
    resolved = []
    for entry in mapping["lessons"][lesson_key]:
        disc, track = entry["disc"], entry["track"]
        item = assets["discs"][disc]["tracks"][str(track)]
        file_id = item["file_id"]
        if not file_id or item["size_bytes"] <= 0:
            raise ValueError(f"Invalid audio metadata for {lesson_key}/{disc}/{track}")
        resolved.append({
            "year": 4,
            "lesson": number,
            "disc": disc,
            "track": track,
            "teacher_book_page": page,
            "drive_file_id": file_id,
            "drive_view_url": f"https://drive.google.com/file/d/{file_id}/view",
            "verification": "metadata_only",
            "delivery_tested": False,
        })
    return resolved


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python resolve_audio_assets.py LESSON_NUMBER")
    try:
        print(json.dumps(resolve_lesson_audio(sys.argv[1]), indent=2))
    except (ValueError, KeyError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
