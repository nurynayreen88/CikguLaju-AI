"""Show the full weekly Lesson range on each matching English RPT block."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import fitz

from .build_web_rpt_weekly_suggestions import ROOT, read_weeks


def add_week_ranges(source, destination):
    dates, weeks = read_weeks(source, "ENGLISH")
    lesson_ids = [lesson for week in sorted(weeks) for lesson in weeks[week][""]]
    if lesson_ids != list(range(1, 161)):
        raise ValueError(f"{source}: expected English Lessons 001-160")

    ranges = {
        week: f" | Lessons {items[''][0]:03d}-{items[''][-1]:03d}"
        for week, items in weeks.items()
    }
    with fitz.open(source) as pdf:
        for page in list(pdf)[1:]:
            for block in page.get_text("dict", clip=fitz.Rect(35, 66, 140, 550))["blocks"]:
                for line in block.get("lines", ()):
                    for span in line["spans"]:
                        match = re.fullmatch(r"M(\d{2})", span["text"])
                        if match is None:
                            continue
                        label = ranges[int(match[1])]
                        x = span["bbox"][2] + 4
                        font = "hebo"
                        size = 6.5
                        if x + fitz.get_text_length(label, fontname=font, fontsize=size) > 134:
                            raise ValueError(f"{source}: Lesson range does not fit the week column")
                        page.insert_text((x, span["origin"][1]), label, fontname=font,
                                         fontsize=size, color=(38/255, 59/255, 78/255))
        pdf.save(destination, deflate=True)

    new_dates, new_weeks = read_weeks(destination, "ENGLISH")
    if dates != new_dates or weeks != new_weeks:
        raise ValueError(f"{source}: weekly dates or Lesson IDs changed")
    with fitz.open(source) as before, fitz.open(destination) as after:
        if len(before) != len(after):
            raise ValueError(f"{source}: page count changed")
        for original, updated in zip(before, after):
            original_text = original.get_text()
            updated_text = updated.get_text()
            suffixes = re.findall(r"\| Lessons \d{3}-\d{3}", updated_text)
            labels = re.findall(r"(?m)^M(\d{2})\s*$", original_text)
            if suffixes != [ranges[int(week)].strip() for week in labels]:
                raise ValueError(f"{source}: unexpected week labels on page {original.number + 1}")
            body = fitz.Rect(140, 0, original.rect.width, original.rect.height)
            if original.get_text(clip=body) != updated.get_text(clip=body):
                raise ValueError(f"{source}: content outside the week column changed")
            if original.number == 0 and original_text != updated_text:
                raise ValueError(f"{source}: cover changed")


def update_english_pdfs(root):
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cover_path = root / "original_cover_layout_verified.json"
    cover = json.loads(cover_path.read_text(encoding="utf-8"))
    cover_hashes = cover["source_sha256_by_subject_year"]
    with TemporaryDirectory(dir=root) as temp:
        pending = []
        for year in range(2, 7):
            key = f"english:{year}"
            record = manifest["files"][key]
            if record["path"] != f"english/tahun_{year}.pdf":
                raise ValueError(f"Unexpected English Year {year} path")
            path = root / record["path"]
            original = path.read_bytes()
            if sha256(original).hexdigest() != record["sha256"] or cover_hashes[key] != record["sha256"]:
                raise ValueError(f"{path}: source disagrees with the release manifest")
            if record.get("week_lesson_ranges_displayed"):
                continue
            updated = Path(temp) / path.name
            add_week_ranges(path, updated)
            content = updated.read_bytes()
            record.update(sha256=sha256(content).hexdigest(), bytes=len(content),
                          week_lesson_ranges_displayed=True)
            cover_hashes[key] = record["sha256"]
            pending.append((updated, path))
        if pending:
            for updated, path in pending:
                updated.replace(path)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                     encoding="utf-8")
            cover_path.write_text(json.dumps(cover, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    update_english_pdfs(parser.parse_args().root)
