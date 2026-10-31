"""Offline validation for Year 4 TB-verified audio mappings.

Run: python rph_standalone/english/year4/validate_audio_mapping.py
Does not access Telegram, Drive, network or production database.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def validate():
    assets = json.loads((HERE / "QA_CLASS_CD_ASSET_MANIFEST_20261031.json").read_text(encoding="utf-8"))
    mapping = json.loads((HERE / "QA_VERIFIED_LESSON_AUDIO_MAPPING_20261031.json").read_text(encoding="utf-8"))
    errors = []
    if assets.get("year") != 4 or mapping.get("year") != 4:
        errors.append("Expected year 4 in both source files")
    if mapping.get("asset_manifest") != "QA_CLASS_CD_ASSET_MANIFEST_20261031.json":
        errors.append("Unexpected audio manifest reference")
    discs = assets.get("discs", {})
    for disc, expected in (("CD1", 88), ("CD2", 88), ("CD3", 44)):
        tracks = discs.get(disc, {}).get("tracks", {})
        if set(tracks) != {str(n) for n in range(1, expected + 1)}:
            errors.append(f"{disc}: missing or extra numbered tracks")
        for number, asset in tracks.items():
            if not isinstance(asset, dict):
                errors.append(f"{disc} Track {number}: metadata must be an object")
                continue
            if not isinstance(asset.get("file_id"), str) or not asset["file_id"] or not isinstance(asset.get("size_bytes"), int) or isinstance(asset["size_bytes"], bool) or asset["size_bytes"] <= 0:
                errors.append(f"{disc} Track {number}: invalid Drive metadata")
    pages = mapping.get("teacher_book_page_by_lesson", {})
    if set(pages) != set(mapping.get("lessons", {})):
        errors.append("Teacher Book page references must match mapped lessons exactly")
    for lesson, page in pages.items():
        if not isinstance(page, int) or isinstance(page, bool) or page <= 0:
            errors.append(f"Lesson {lesson}: invalid Teacher Book page")
    all_ids = []
    for disc_info in discs.values():
        all_ids.extend(asset.get("file_id") for asset in disc_info.get("tracks", {}).values() if isinstance(asset, dict))
    if len(all_ids) != len(set(all_ids)):
        errors.append("Drive file ID is reused across different manifest tracks")
    usages = []
    for lesson, items in mapping.get("lessons", {}).items():
        if not (isinstance(lesson, str) and len(lesson) == 3 and lesson.isascii() and lesson.isdecimal() and 1 <= int(lesson) <= 160):
            errors.append(f"Invalid lesson key: {lesson}")
        if not isinstance(items, list) or not items:
            errors.append(f"Lesson {lesson}: empty or invalid mapping list")
            continue
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                errors.append(f"Lesson {lesson}: mapping entry must be an object")
                continue
            disc, track = item.get("disc"), item.get("track")
            if not isinstance(disc, str) or disc not in ("CD1", "CD2", "CD3"):
                errors.append(f"Lesson {lesson}: invalid disc {disc!r}")
                continue
            if not isinstance(track, int) or isinstance(track, bool):
                errors.append(f"Lesson {lesson}: invalid track {track!r}")
                continue
            key = (disc, track)
            if key in seen:
                errors.append(f"Lesson {lesson}: duplicate mapping {key}")
            seen.add(key)
            asset = discs.get(disc, {}).get("tracks", {}).get(str(track))
            if asset is None:
                errors.append(f"Lesson {lesson}: missing or null {disc} Track {track}")
                continue
            if not isinstance(asset, dict) or not isinstance(asset.get("file_id"), str):
                errors.append(f"Lesson {lesson}: invalid asset metadata for {disc} Track {track}")
                continue
            usages.append((lesson, disc, track, asset["file_id"]))
    print(f"Lessons: {len(mapping.get('lessons', {}))}; track usages: {len(usages)}; unique MP3s: {len({u[3] for u in usages})}; errors: {len(errors)}")
    for error in errors:
        print("ERROR:", error)
    return not errors


if __name__ == "__main__":
    raise SystemExit(0 if validate() else 1)
