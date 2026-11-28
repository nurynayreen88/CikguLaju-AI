"""Paid editable Word for the two exact DPK RPT sources; no PDF changes."""
from hashlib import sha256
from pathlib import Path
import json
from web import rpt_native_word_batch as native_word
from rpt_2027.matematik import sk_documents

def eligible(year, *, root):
    if not native_word.enabled() or year not in sk_documents.DPK_DIGESTS:
        return False
    try:
        source=sk_documents.document_path(year,root=Path(root)/"matematik",dpk=True)
        if source is None:
            return False
        from web.rpt_native_word_cover import selected_layout
        lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))
        selected_layout(lock,f"matematik_dpk:{year}",sk_documents.DPK_DIGESTS[year])
        return True
    except (OSError,ValueError,KeyError,TypeError):
        return False

def document(year,account,config,*,root):
    from web.english_rpt_2027_http import _has_paid_access
    if not _has_paid_access(account):
        raise PermissionError("Paid RPT Word only")
    if not eligible(year,root=root):
        raise ValueError("DPK source unavailable or changed")
    from tools.build_rpt_math_dpk_native_word_20261127 import build_word
    from web.rpt_native_word_cover import personalized_word
    blob,raw,expected=build_word(year,root=root)
    digest=sha256(raw).hexdigest()
    if digest!=sk_documents.DPK_DIGESTS[year] or len(expected)!=117:
        raise ValueError("DPK source or lesson count changed")
    lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))
    result=personalized_word(blob,raw,lock,f"matematik_dpk:{year}",account,config)
    return result,digest
