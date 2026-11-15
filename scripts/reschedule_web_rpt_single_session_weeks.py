"""Move single-session Muzik and RBT plans off fully closed weeks."""
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import fitz

from .build_english_rpt_weekly_allocation import CALENDAR, CLOSED_WEEKS, FONT_DIR
from .build_web_rpt_weekly_suggestions import ROOT, read_weeks


SUBJECTS = {"muzik": ("MUZIK", range(2, 7), 35), "rbt": ("RBT", range(4, 7), 32)}
WEEK_COLUMN = fitz.Rect(35, 78.6, 140, 558)


def move_from_holidays(weeks):
    scheduled = []
    for original in sorted(weeks):
        week = max(original, scheduled[-1] + 1) if scheduled else original
        while week in CLOSED_WEEKS:
            week += 1
        if week > 44:
            raise ValueError("Insufficient available weeks")
        scheduled.append(week)
    return dict(zip(sorted(weeks), scheduled))


def date_label(value):
    return date.fromisoformat(value).strftime("%d/%m/%Y")


def revise(source, target, code, total, calendar):
    _, original = read_weeks(source, code)
    if list(original.values()) != [{"": [n]} for n in range(1, total + 1)]:
        raise ValueError(f"{source}: expected a single PdP per row, in order")
    reassigned = move_from_holidays(original)
    with fitz.open(source) as pdf:
        for page in list(pdf)[1:]:
            changes = []
            for drawing in page.get_drawings():
                rect = drawing["rect"]
                if (drawing["type"] != "f" or abs(rect.x0 - WEEK_COLUMN.x0) > 0.1
                        or abs(rect.width - WEEK_COLUMN.width) > 0.1):
                    continue
                items = [s for b in page.get_text("dict", clip=rect)["blocks"]
                         for line in b.get("lines", ()) for s in line["spans"]]
                old = int(items[0]["text"][1:])
                new = reassigned[old]
                if old == new:
                    continue
                if len(items) != 5 or [items[i]["text"] for i in (1, 3)] != ["Kumpulan A:", "Kumpulan B:"]:
                    raise ValueError(f"{source}: unexpected week cell for M{old:02d}")
                changes.append((items[0], f"M{new:02d}"))
                for pos, group in ((2, "A"), (4, "B")):
                    row = calendar[group][new - 1]
                    changes.append((items[pos], " - ".join(date_label(row[key]) for key in ("start", "end"))))
            if not changes:
                continue
            for span, _ in changes:
                page.add_redact_annot(span["bbox"], fill=False)
            page.apply_redactions(images=0, graphics=0, text=0)
            page.insert_font(fontname="RPTWeek", fontfile=str(FONT_DIR / "DejaVuSans.ttf"))
            for span, text in changes:
                color = tuple(((span["color"] >> shift) & 255) / 255 for shift in (16, 8, 0))
                page.insert_text(span["origin"], text, fontsize=span["size"], fontname="RPTWeek", color=color)
        pdf.subset_fonts()
        pdf.save(target, deflate=True, garbage=4)
    dates, updated = read_weeks(target, code)
    expected = {reassigned[week]: ids for week, ids in original.items()}
    if dict(updated) != expected:
        raise ValueError(f"{source}: the new PDF does not match the proposed weeks")
    for week, actual in dates.items():
        expected_dates = tuple(calendar[group][week - 1][key]
                               for group in ("A", "B") for key in ("start", "end"))
        if actual != expected_dates:
            raise ValueError(f"{source}: M{week:02d} date mismatch")
    with fitz.open(source) as before, fitz.open(target) as after:
        if before.page_count != after.page_count or before[0].get_pixmap().samples != after[0].get_pixmap().samples:
            raise ValueError(f"{source}: cover or pagination changed")
        for original_page, updated_page in zip(list(before)[1:], list(after)[1:]):
            body = fitz.Rect(140, 0, original_page.rect.width, original_page.rect.height)
            if original_page.get_text(clip=body) != updated_page.get_text(clip=body):
                raise ValueError(f"{source}, p{original_page.number + 1}: teaching content changed")


def main():
    calendar = json.loads(CALENDAR.read_text(encoding="utf-8"))["weeks"]
    manifest_file = ROOT / "manifest.json"
    cover_file = ROOT / "original_cover_layout_verified.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    cover = json.loads(cover_file.read_text(encoding="utf-8"))
    with TemporaryDirectory(dir=ROOT) as temp:
        targets = []
        for subject, (code, years, total) in SUBJECTS.items():
            for year in years:
                key = f"{subject}:{year}"
                record = manifest["files"][key]
                source = ROOT / record["path"]
                raw = source.read_bytes()
                if sha256(raw).hexdigest() != record["sha256"] or record["sha256"] != cover["source_sha256_by_subject_year"][key]:
                    raise ValueError(f"Source and cover hashes disagree for {source}")
                if record.get("full_school_closures_rescheduled"):
                    continue
                target = Path(temp) / f"{subject}_{year}.pdf"
                revise(source, target, code, total, calendar)
                raw = target.read_bytes()
                record.update(bytes=len(raw), sha256=sha256(raw).hexdigest(), full_school_closures_rescheduled=True)
                cover["source_sha256_by_subject_year"][key] = record["sha256"]
                targets.append((target, source))
        if targets:
            for target, source in targets:
                target.replace(source)
            for path, data in ((manifest_file, manifest), (cover_file, cover)):
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
