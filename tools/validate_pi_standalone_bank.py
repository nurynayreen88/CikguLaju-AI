"""Read-only validator for pre-approved Pendidikan Islam standalone RPH PDFs.

Manifest example:
{"schema_version":1,"items":[{"year":1,"lesson_id":"PI-Y1-L001",
"sk":"1.1","sp":"1.1.1","pdf":"pdf/PI-Y1-L001.pdf",
"sha256":"<64 hex>","status":"approved"}]}

No database writes, no PDF generation and no live bot integration.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ALLOWED_STATUS = {"draft", "review", "approved"}
LESSON_ID = re.compile(r"^PI-Y[1-6]-L[0-9]{3,4}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate(manifest_path: Path):
    root = manifest_path.parent.resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("items"), list):
        raise ValueError("Invalid manifest schema")
    seen = set()
    errors = []
    approved = 0
    for index, item in enumerate(data["items"], 1):
        tag = f"item {index}"
        if not isinstance(item, dict):
            errors.append(f"{tag}: expected object")
            continue
        year, lesson = item.get("year"), item.get("lesson_id")
        if type(year) is not int or year not in range(1, 7):
            errors.append(f"{tag}: invalid year")
        if not isinstance(lesson, str) or not LESSON_ID.fullmatch(lesson):
            errors.append(f"{tag}: invalid lesson_id")
        elif isinstance(year, int) and not lesson.startswith(f"PI-Y{year}-"):
            errors.append(f"{tag}: year/lesson mismatch")
        if lesson in seen:
            errors.append(f"{tag}: duplicate lesson_id {lesson}")
        seen.add(lesson)
        if not all(isinstance(item.get(k), str) and item[k].strip() for k in ("sk", "sp")):
            errors.append(f"{tag}: missing SK/SP")
        status = item.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{tag}: invalid status")
        rel = item.get("pdf")
        if not isinstance(rel, str) or not rel.lower().endswith(".pdf"):
            errors.append(f"{tag}: invalid PDF path")
            continue
        path = (root / rel).resolve()
        if not path.is_relative_to(root) or path == root:
            errors.append(f"{tag}: path escapes bank")
            continue
        if status == "approved":
            approved += 1
            digest = item.get("sha256")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                errors.append(f"{tag}: approved PDF missing valid SHA256")
            if not path.is_file():
                errors.append(f"{tag}: approved PDF missing")
            else:
                if path.read_bytes()[:5] != b"%PDF-":
                    errors.append(f"{tag}: invalid PDF header")
                else:
                    try:
                        import fitz
                        with fitz.open(path) as document:
                            if len(document) != 1:
                                errors.append(f"{tag}: approved RPH must be one A4 page")
                            for page in document:
                                if abs(page.rect.width - 595.28) > 2 or abs(page.rect.height - 841.89) > 2:
                                    errors.append(f"{tag}: approved RPH must use A4 portrait")
                                for image in page.get_image_info():
                                    x0, y0, x1, y1 = image["bbox"]
                                    if x0 < -0.5 or y0 < -0.5 or x1 > page.rect.width + 0.5 or y1 > page.rect.height + 0.5:
                                        errors.append(f"{tag}: image extends outside page")
                    except Exception as exc:
                        errors.append(f"{tag}: PDF cannot be opened: {type(exc).__name__}")
                if isinstance(digest, str) and SHA256.fullmatch(digest):
                    actual = hashlib.sha256(path.read_bytes()).hexdigest()
                    if actual != digest:
                        errors.append(f"{tag}: PDF checksum mismatch")
    return {"total": len(data["items"]), "approved": approved, "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    result = validate(args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["errors"] else 0)


if __name__ == "__main__":
    main()
