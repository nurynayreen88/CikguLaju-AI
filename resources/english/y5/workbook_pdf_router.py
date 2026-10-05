# CikguLaju English Year 5 Workbook PDF-part router
# Non-destructive companion to workbook_verified_map.py.
# Workbook printed-page -> source PDF page was visually verified on 2026-10-05:
# printed p5 = original PDF page 4, printed p7 = original PDF page 6.
# Therefore original_pdf_page = printed_page - 1.

EN5_WB_PDF_PARTS = (
    (1, 54, "books/english/y5_workbook_001_054.pdf"),
    (55, 110, "books/english/y5_workbook_055_110.pdf"),
)

def _expand_page_spec(page_spec):
    pages = []
    for token in str(page_spec).split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(token))
    return sorted(set(pages))

def printed_to_original_pdf_page(printed_page):
    return int(printed_page) - 1

def locate_original_pdf_page(original_pdf_page):
    p = int(original_pdf_page)
    for start, end, path in EN5_WB_PDF_PARTS:
        if start <= p <= end:
            return {
                "path": path,
                "original_pdf_page": p,
                "part_page": p - start + 1,
            }
    raise ValueError(f"Year 5 Workbook PDF page out of range: {p}")

def resolve_printed_pages(page_spec):
    out = []
    for printed_page in _expand_page_spec(page_spec):
        original = printed_to_original_pdf_page(printed_page)
        item = locate_original_pdf_page(original)
        item["printed_page"] = printed_page
        out.append(item)
    return out

def resolve_lesson(lesson):
    from .workbook_verified_map import EN5_WB_VERIFIED
    row = EN5_WB_VERIFIED.get(int(lesson))
    if not row:
        return []
    return resolve_printed_pages(row[0])
