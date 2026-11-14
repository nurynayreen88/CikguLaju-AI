"""Build the Year 2 DLP review catalog from the lesson plans used for sign-off."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "staging" / "dlp" / "year2"
CATALOG = ROOT / "data" / "dlp_year2_review.json"
FIELDS = {
    "Standards": "standards",
    "References": "references",
    "Learning objective": "objective",
    "Materials": "materials",
    "Reflection": "reflection",
}
SUBJECTS = {"SCI": "SCIENCE_DLP", "MAT": "MATH_DLP"}
HEADER = re.compile(r"^## (DLP-(SCI|MAT)-Y2-U(\d{2})-\d{2}) · (.+)$", re.M)


def build_catalog():
    subjects = {code: {} for code in SUBJECTS.values()}
    seen = set()
    for path in sorted(SOURCE.glob("*.md")):
        source = path.read_text(encoding="utf-8")
        unit_heading = re.search(r"^# .+? · (Unit ([1-9]\d*) [^\n·]+)", source, re.M)
        if not unit_heading:
            raise ValueError(f"Missing unit heading in {path}")
        unit_name = unit_heading[1].strip()
        unit_id = unit_heading[2].zfill(2)
        sections = list(HEADER.finditer(source))
        if not sections:
            raise ValueError(f"No lessons in {path}")
        for index, match in enumerate(sections):
            lesson_id, subject, unit, title = match.groups()
            if unit != unit_id:
                raise ValueError(f"{lesson_id}: unit differs from the heading in {path}")
            end = sections[index + 1].start() if index + 1 < len(sections) else len(source)
            body = source[match.end():end]
            if lesson_id in seen:
                raise ValueError(f"Duplicate lesson {lesson_id}")
            seen.add(lesson_id)
            entry = {"id": lesson_id, "title": title}
            for label, field in FIELDS.items():
                value = re.search(rf"^\*\*{re.escape(label)}\*\* · (.+)$", body, re.M)
                if not value:
                    raise ValueError(f"{lesson_id}: missing {label}")
                entry[field] = value[1].strip()
            phases = re.findall(r"^\| ([^|]+? · \d+ min) \| ([^|]+) \| ([^|]+) \|$", body, re.M)
            if len(phases) != 4 or sum(int(re.search(r"(\d+) min$", row[0])[1]) for row in phases) != 60:
                raise ValueError(f"{lesson_id}: invalid phases")
            entry["phases"] = [list(row) for row in phases]
            group = subjects[SUBJECTS[subject]].setdefault(unit, {"id": unit, "title": unit_name, "lessons": []})
            if group["title"] != unit_name:
                raise ValueError(f"{lesson_id}: inconsistent unit title")
            group["lessons"].append(entry)

    for groups in subjects.values():
        for group in groups.values():
            group["lessons"].sort(key=lambda row: row["id"])
    return {subject: list(sorted(groups.values(), key=lambda row: row["id"])) for subject, groups in subjects.items()}


def navigation(catalog):
    return {
        code: [{"id": unit["id"], "title": unit["title"], "lessons": [
            {"id": lesson["id"], "title": lesson["title"]} for lesson in unit["lessons"]
        ]} for unit in units]
        for code, units in catalog.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the committed catalog against its lesson plans.")
    parser.add_argument("--web-index", type=Path, help="Update the navigation in the Web release HTML.")
    args = parser.parse_args()
    catalog = build_catalog()
    data = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    web_data = json.dumps(navigation(catalog), ensure_ascii=False, separators=(",", ":"))
    if args.check:
        if CATALOG.read_text(encoding="utf-8") != data + "\n":
            parser.error("Review catalog differs from the source lesson plans.")
        if args.web_index:
            expected = web_data.replace("<", "\\u003c")
            if f'<script id="dlp-navigation-data" type="application/json">{expected}</script>' not in args.web_index.read_text(encoding="utf-8"):
                parser.error("Embedded Web navigation differs from the source lesson plans.")
        return
    CATALOG.write_text(data + "\n", encoding="utf-8")
    if args.web_index:
        page = args.web_index.read_text(encoding="utf-8")
        payload = web_data.replace("<", "\\u003c")
        page, count = re.subn(
            r'(<script id="dlp-navigation-data" type="application/json">).*?(</script>)',
            lambda match: match[1] + payload + match[2], page, count=1, flags=re.S,
        )
        if count != 1:
            parser.error("Web navigation placeholder missing.")
        args.web_index.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
