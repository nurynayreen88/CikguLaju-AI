"""Read-only inspection of an actual bot-delivered Pendidikan Islam RPH PDF.

Usage: python tools/audit_pi_jawi_pdf.py path/to/bot-delivered.pdf
This is a structural gate, NOT visual approval of Jawi shaping.
"""
import argparse
import hashlib
import json
from pathlib import Path


def inspect_pdf(path):
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("Install PyMuPDF to inspect PDF geometry") from exc
    pdf_path = Path(path)
    data = pdf_path.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise ValueError("Not a PDF file")
    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    for page in doc:
        rect = page.rect
        text = page.get_text("text")
        images = page.get_images(full=True)\n        image_blocks = [b for b in page.get_text("dict").get("blocks", []) if b.get("type") == 1]
        blocks = page.get_text("dict").get("blocks", [])
        outside = []
        for block in blocks:
            bbox = block.get("bbox")
            if bbox and (bbox[0] < -0.5 or bbox[1] < -0.5
                         or bbox[2] > rect.width + 0.5
                         or bbox[3] > rect.height + 0.5):
                outside.append(list(bbox))
        pages.append({
            "width_pt": round(rect.width, 2),
            "height_pt": round(rect.height, 2),
            "a4_portrait": abs(rect.width - 595.28) < 3 and abs(rect.height - 841.89) < 3,
            "text_chars": len(text),
            "arabic_text_chars": sum(0x0600 <= ord(ch) <= 0x08FF for ch in text),
            "image_count": len(images),\n            "placed_image_blocks": len(image_blocks),
            "out_of_page_text_blocks": outside,
        })
    doc.close()
    return {
        "file": str(pdf_path),
        "sha256": hashlib.sha256(data).hexdigest(),
        "page_count": len(pages),
        "pages": pages,
        "structural_pass": len(pages) == 1 and all(
            p["a4_portrait"] and not p["out_of_page_text_blocks"]
            and (p["text_chars"] > 0 or p["placed_image_blocks"] > 0)
            for p in pages
        ),
        "jawi_visual_approval": "NOT_ASSESSED",
        "note": "Image-based Jawi may have zero extractable Arabic characters. Inspect rasterized PDF manually; this script cannot validate joining or RTL order.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args()
    result = inspect_pdf(args.pdf)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    return 0 if result["structural_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
