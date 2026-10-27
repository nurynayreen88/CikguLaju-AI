"""Read-only Jawi RPH PDF layout audit. Requires PyMuPDF.
Usage: python tools/check_rph_pdf_layout.py input.pdf [--output report.json]
No OCR, application imports, or database access.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
import fitz

def inspect_pdf(path):
    document = fitz.open(path)
    pages = []
    for page in document:
        images = page.get_image_info(xrefs=True)
        heights = [round(i["bbox"][3] - i["bbox"][1], 2) for i in images]
        overflows = [
            {"image": index + 1, "bbox": [round(v, 2) for v in item["bbox"]]}
            for index, item in enumerate(images)
            if item["bbox"][0] < -0.5 or item["bbox"][1] < -0.5
            or item["bbox"][2] > page.rect.width + 0.5
            or item["bbox"][3] > page.rect.height + 0.5
        ]
        pages.append({
            "page": page.number + 1,
            "width_pt": round(page.rect.width, 2),
            "height_pt": round(page.rect.height, 2),
            "embedded_image_count": len(images),
            "selectable_character_count": len(page.get_text().strip()),
            "image_height_pt_counts": dict(sorted(
                Counter(str(h) for h in heights).items(),
                key=lambda x: float(x[0]))),
            "images_under_13pt": sum(h < 13 for h in heights),
            "image_page_overflows": overflows,
        })
    document.close()
    return {"pdf": Path(path).name, "pages": pages,
            "note": "Image height is not actual font size; visually review output."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(inspect_pdf(args.pdf), ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(result + "\n", encoding="utf-8")
    print(result)

if __name__ == "__main__":
    main()
