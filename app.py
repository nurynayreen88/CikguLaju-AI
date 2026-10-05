

# ===== v25.263 ENGLISH Y5/Y6 WORKBOOK PDF-PART ROUTING =====
# Non-destructive late runtime helper. Resolves verified Workbook printed pages
# to the exact Git PDF part + page within that part. Existing T1-T4 routing,
# v25.262 page mapping and RPH formatting remain unchanged.
APP_VERSION='v25.263-ENGLISH-Y5Y6-WORKBOOK-PDF-PART-ROUTING'
import runpy as _runpy_v25263, os as _os_v25263

def _en25263_load_router(rel):
    try:
        p=_os_v25263.path.join(_os_v25263.path.dirname(__file__),rel)
        return _runpy_v25263.run_path(p)
    except Exception:
        return {}

_EN5_WB_ROUTER_V25263=_en25263_load_router('resources/english/y5/workbook_pdf_router.py')
_EN6_WB_ROUTER_V25263=_en25263_load_router('resources/english/y6/workbook_pdf_router.py')

def _en_workbook_pdf_parts_v25263(ss):
    """Return exact Git PDF-part locations for the selected verified Y5/Y6 lesson."""
    try:
        if not _en_primary_v25232(ss):
            return []
        y=_english_primary_year_number_v2517((ss or {}).get('year'))
        if y not in (5,6):
            return []
        lesson=int((ss or {}).get('lesson_no') or (ss or {}).get('lesson') or (ss or {}).get('textbook_lesson_no'))
        router=_EN5_WB_ROUTER_V25263 if y==5 else _EN6_WB_ROUTER_V25263
        resolver=router.get('resolve_lesson')
        if not callable(resolver):
            return []
        rows=resolver(lesson) or []
        # Defensive validation: expose only known repository Workbook parts.
        prefix='books/english/y5_workbook_' if y==5 else 'books/english/y6_workbook_'
        out=[]
        for row in rows:
            if not isinstance(row,dict):
                continue
            path=str(row.get('path') or '')
            if not path.startswith(prefix) or not path.endswith('.pdf'):
                continue
            out.append({
                'year':y,
                'lesson':lesson,
                'resource_type':'workbook',
                'printed_page':int(row['printed_page']),
                'original_pdf_page':int(row['original_pdf_page']),
                'pdf_part_path':path,
                'pdf_part_page':int(row['part_page']),
                'verified':1,
            })
        return out
    except Exception:
        return []

def _en_workbook_pdf_part_groups_v25263(ss):
    """Group resolved pages by PDF part for download/snapshot senders."""
    grouped={}
    for row in _en_workbook_pdf_parts_v25263(ss):
        path=row['pdf_part_path']
        g=grouped.setdefault(path,{
            'path':path,
            'printed_pages':[],
            'part_pages':[],
            'original_pdf_pages':[],
            'verified':1,
        })
        g['printed_pages'].append(row['printed_page'])
        g['part_pages'].append(row['pdf_part_page'])
        g['original_pdf_pages'].append(row['original_pdf_page'])
    return list(grouped.values())

CIKGULAJU_PATCH_V25263='ENGLISH_Y5Y6_WORKBOOK_PDF_PART_ROUTING'
# ===== END v25.263 =====
