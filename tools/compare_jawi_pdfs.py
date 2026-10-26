"""Compare rasterized RPH PDFs by image content and page placement.

Usage: python tools/compare_jawi_pdfs.py old.pdf new.pdf
Read-only; no app import or database access.
"""
import hashlib
import sys
import fitz

def inventory(path):
    doc = fitz.open(path)
    page = doc[0]
    rows = []
    for entry in page.get_images(full=True):
        blob = doc.extract_image(entry[0])["image"]
        digest = hashlib.sha256(blob).hexdigest()
        for rect in page.get_image_rects(entry[0]):
            rows.append((tuple(round(v, 1) for v in rect), digest))
    return rows, len(page.get_text().strip())

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python tools/compare_jawi_pdfs.py old.pdf new.pdf")
    old, old_text = inventory(sys.argv[1])
    new, new_text = inventory(sys.argv[2])
    old_hashes = {digest for _, digest in old}
    new_hashes = {digest for _, digest in new}
    old_at = dict(old)
    new_at = dict(new)
    same_position = set(old_at) & set(new_at)
    unchanged_at_position = sum(old_at[pos] == new_at[pos] for pos in same_position)
    print("Raster images:", len(old), len(new))
    print("Extractable text lengths:", old_text, new_text)
    print("Identical image contents (unique):", len(old_hashes & new_hashes))
    print("Matching placements:", len(same_position))
    print("Identical images at same placement:", unchanged_at_position)
    print("Changed/new placements:", len(set(new_at) - set(old_at)))
    print("Changed content at matching placements:",
          sum(old_at[p] != new_at[p] for p in same_position))

if __name__ == "__main__":
    main()
