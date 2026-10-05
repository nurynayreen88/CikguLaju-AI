# CikguLaju English Year 6 Workbook PDF-part router
# Non-destructive companion to workbook_verified_map.py.
# Workbook printed-page -> source PDF page was visually verified on 2026-10-05:
# printed p2 = original PDF page 4, printed p4 = original PDF page 6.
# Therefore original_pdf_page = printed_page + 2.

EN6_WB_PDF_PARTS = (
    (1, 40, "books/english/y6_workbook_001_040.pdf"),
    (41, 80, "books/english/y6_workbook_041_080.pdf"),
    (81, 116, "books/english/y6_workbook_081_116.pdf"),
    (117, 131, "books/english/y6_workbook_117_131.pdf"),
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
    return int(printed_page) + 2

def locate_original_pdf_page(original_pdf_page):
    p = int(original_pdf_page)
    for start, end, path in EN6_WB_PDF_PARTS:
        if start <= p <= end:
            return {
                "path": path,
                "original_pdf_page": p,
                "part_page": p - start + 1,
            }
    raise ValueError(f"Year 6 Workbook PDF page out of range: {p}")

def resolve_printed_pages(page_spec):
    out = []
    for printed_page in _expand_page_spec(page_spec):
        original = printed_to_original_pdf_page(printed_page)
        item = locate_original_pdf_page(original)
        item["printed_page"] = printed_page
        out.append(item)
    return out

def resolve_lesson(lesson):
    from .workbook_verified_map import EN6_WB_VERIFIED
    page_spec = EN6_WB_VERIFIED.get(int(lesson))
    if not page_spec:
        return []
    return resolve_printed_pages(page_spec)
