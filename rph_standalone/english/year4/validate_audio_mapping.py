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
            if not asset.get("file_id") or not isinstance(asset.get("size_bytes"), int) or asset["size_bytes"] <= 0:
                errors.append(f"{disc} Track {number}: invalid Drive metadata")
    pages = mapping.get("teacher_book_page_by_lesson", {})
    if set(pages) != set(mapping.get("lessons", {})):
        errors.append("Teacher Book page references must match mapped lessons exactly")
    for lesson, page in pages.items():
        if not isinstance(page, int) or isinstance(page, bool) or page <= 0:
            errors.append(f"Lesson {lesson}: invalid Teacher Book page")
    all_ids = []
    for disc_info in discs.values():
        all_ids.extend(asset.get("file_id") for asset in disc_info.get("tracks", {}).values())
    if len(all_ids) != len(set(all_ids)):
        errors.append("Drive file ID is reused across different manifest tracks")
    usages = []
    for lesson, items in mapping.get("lessons", {}).items():
        if not (len(lesson) == 3 and lesson.isdigit() and 1 <= int(lesson) <= 160):
            errors.append(f"Invalid lesson key: {lesson}")
        if not items:
            errors.append(f"Lesson {lesson}: empty mapping")
        seen = set()
        for item in items:
            disc, track = item.get("disc"), item.get("track")
            key = (disc, track)
            if key in seen:
                errors.append(f"Lesson {lesson}: duplicate mapping {key}")
            seen.add(key)
            if not isinstance(track, int) or isinstance(track, bool):
                errors.append(f"Lesson {lesson}: invalid track {track!r}")
                continue
            asset = discs.get(disc, {}).get("tracks", {}).get(str(track))
            if not asset:
                errors.append(f"Lesson {lesson}: missing {disc} Track {track}")
                continue
            usages.append((lesson, disc, track, asset["file_id"]))
    print(f"Lessons: {len(mapping.get('lessons', {}))}; track usages: {len(usages)}; unique MP3s: {len({u[3] for u in usages})}; errors: {len(errors)}")
    for error in errors:
        print("ERROR:", error)
    return not errors


if __name__ == "__main__":
    raise SystemExit(0 if validate() else 1)
