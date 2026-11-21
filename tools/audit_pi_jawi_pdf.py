"""Read-only inspection of an actual bot-delivered Pendidikan Islam RPH PDF.

Usage: python tools/audit_pi_jawi_pdf.py path/to/bot-delivered.pdf
This is a structural gate, NOT visual approval of Jawi shaping.
"""
import argparse
import hashlib
import json
from pathlib import Path



def _grid_alignment(page):
    """Conservative PDF vector-rule check; NOT Jawi glyph or content approval.

    LibreOffice may emit table borders as separate line strokes, while PyMuPDF
    may expose rectangles. Rejoin only adjacent horizontal segments on the
    same baseline. Do not guess success when the PDF lacks enough vectors.
    """
    import fitz

    strokes = []
    for drawing in page.get_drawings():
        if "s" not in drawing.get("type", ""):
            continue
        for item in drawing.get("items", ()):
            if item[0] == "l":
                p1, p2 = item[1], item[2]
                if abs(p1.y - p2.y) <= 0.7 and abs(p1.x - p2.x) >= 2:
                    strokes.append(((p1.y + p2.y) / 2, min(p1.x, p2.x), max(p1.x, p2.x)))
            elif item[0] == "re":
                rect = fitz.Rect(item[1])
                if rect.width >= 2:
                    strokes.extend(((rect.y0, rect.x0, rect.x1),
                                    (rect.y1, rect.x0, rect.x1)))

    # Group close Y-coordinates; reconstruct a full horizontal grid rule
    # from contiguous segments without bridging real gaps between boxes.
    rows = []
    for y, left, right in sorted(strokes):
        if not rows or abs(y - rows[-1][0]) > 0.8:
            rows.append([y, []])
        rows[-1][1].append((left, right))

    full_width_rules = []
    for y, spans in rows:
        merged = []
        for left, right in sorted(spans):
            if merged and left <= merged[-1][1] + 2.5:
                merged[-1][1] = max(merged[-1][1], right)
            else:
                merged.append([left, right])
        long = [pair for pair in merged if pair[1] - pair[0] >= page.rect.width * 0.75]
        if long:
            full_width_rules.append((y, *max(long, key=lambda pair: pair[1] - pair[0])))

    # Fewer than four horizontal borders cannot establish that several
    # main boxes share the same left/right outer edges. Image-only PDFs
    # and unusual vector representations remain NOT_ASSESSED, not PASS.
    result = {"status": "NOT_ASSESSED", "full_width_rule_count": len(full_width_rules),
              "left_edge_drift_pt": None, "right_edge_drift_pt": None}
    if len(full_width_rules) < 4:
        return result

    left_drift = max(line[1] for line in full_width_rules) - min(line[1] for line in full_width_rules)
    right_drift = max(line[2] for line in full_width_rules) - min(line[2] for line in full_width_rules)
    result.update(status="ALIGNED" if max(left_drift, right_drift) <= 2.0 else "MISALIGNED",
                  left_edge_drift_pt=round(left_drift, 2),
                  right_edge_drift_pt=round(right_drift, 2))
    return result


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
        images = page.get_images(full=True)
        image_blocks = [b for b in page.get_text("dict").get("blocks", []) if b.get("type") == 1]
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
            "image_count": len(images),
            "placed_image_blocks": len(image_blocks),
            "out_of_page_text_blocks": outside,
            "grid_alignment": _grid_alignment(page),
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
        "note": "Grid alignment is a separate vector diagnostic, not proof of every box. Image-only or ambiguous PDFs remain NOT_ASSESSED. Inspect rasterized Jawi manually for glyph joining/RTL order; structural_pass does not authorize publication.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("--output", help="Optional JSON report path")
    parser.add_argument("--require-aligned-grid", action="store_true",
                        help="Fail closed unless multiple full-width grid rules have matching outer edges")
    args = parser.parse_args()
    result = inspect_pdf(args.pdf)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    aligned = all(p["grid_alignment"]["status"] == "ALIGNED" for p in result["pages"])
    return 0 if result["structural_pass"] and (not args.require_aligned_grid or aligned) else 1


if __name__ == "__main__":
    raise SystemExit(main())
