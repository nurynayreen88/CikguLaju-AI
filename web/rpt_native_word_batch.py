"""Opt-in paid Word from exact 31 layout-QA sources; leave PDF routes untouched."""
import hashlib
import json
import os
from pathlib import Path

PINS = {
    "pendidikan_moral:2": "77f60c620a84775eaf946e199da8870c6e0923274ea2b5680aa1fc06a93e272a",
    "pendidikan_moral:3": "546a4bb5b25a5c84f5db5006697bd8af22e8765dc8cf1e0561cf5481f4506cb4",
    "pendidikan_moral:4": "485c98504de7a24c8f82194713db1c8c5686bf22b2a0e7f9e905655d7459ca03",
    "pendidikan_moral:5": "b06700f5a39576638fbc490a8a351efbcf2cc62022f09e1299ce751a4d04c1a6",
    "pendidikan_moral:6": "8ef07730b1d50e8f36e61497b3b87ddb6a833a7bbf04f1d540f05f460ea4294d",
    "pjpk:2": "6b4896600a55b9c6ef9e759eafc5243c16fea7da1b30a7857b0d2ff447015705",
    "pjpk:3": "33aa07b8347a15aae8955d2151c046eeb9c77b5f34014e6ff597258d68e45be3",
    "pjpk:4": "4d635dcc07f8ddb85723390a5f3c6d42142965c070205aead0ff788afa388504",
    "pjpk:5": "2a3d3a905f19001e3ddbe15a79dbd876be3e9e4298f6ab4602d5a610508386e7",
    "pjpk:6": "df2a8a1bf6276d652c6c924887fbf8e02695a1d67e81eac241f8c513f49fc0d0",
    "psv:2": "b0fdd7aa6f3569692130151859c1c0d10cfed71d969f40bf9ca5bd88565e1a4a",
    "psv:3": "bf434209d5e75a450aa1ce30d92e4e1210d9e3d480d64b93117c54d571fd8765",
    "psv:4": "063041453269d161f246cfeaafcdab97f6ad608981c5cb01ff0162548ea8ae40",
    "psv:5": "5f49b0d27bac20c9e3131ae63c8fa19fd7d00e0c8419765677291f5abbc5cd81",
    "psv:6": "91de6e92c2d807f6c38a0de4e3776391e08c92798f126148c3a548ad06010a16",
    "muzik:2": "0bc94d264fd372ed8977fa65db4f2177864e2684465e7a700688398e94936a5b",
    "muzik:3": "7b78a82a30327c44a8673d613eafdba4e4b882ca5acb34d078be2d9fbdcb97a4",
    "muzik:4": "ffa2f013b54b838e91bbe5498dabd3ebb3ebd9b2a197e88ba5ab2b3c332bb958",
    "muzik:5": "0341ef735063d84d909823bce8d41269be7f540fa4472eda1a9f9f5b3958e385",
    "muzik:6": "b26671282b6843c735fa3e2bfe5d936537bc58c47f36e18f5d43ab0d83048210",
    "rbt:4": "9ea854b7f0c863d51c33af4403cbc1638d8b954be9e604620970563879d398ee",
    "rbt:5": "2f80ed3a03ad562af9b7d4e3076330f836f7faa6298ffa8e92d6708faa2a9ffd",
    "rbt:6": "8f8ec00e915bbc9757f6886dd16c2e8e79c874f4b1cef384f7580de4e4401500",
    "sejarah:4": "b02475784a2611a730b64c825aeae8c437b22c09ad0c8bd458e0fdcba2ed2742",
    "sejarah:5": "70dc0c6d2e22ab80486ba51c9fbac1c0548d82d062c05ab9294b4afde1a58519",
    "sejarah:6": "c4acfae098d482be802d9432985263da71ba302dfd39eeb6f560e18c940532b7",
    "sains:2": "0fd06eea9867fa67d2afb898d99a397a74984b578e4f1490be7a3daec16e4386",
    "sains:3": "06cb134948b6ae8e68fc3bc03a2ce5df425df92a9d803dcc05951471d8786fd9",
    "sains:4": "05fb79906df3b0c27df77f0c747265980137440382b6b3c22c66c0e689115efa",
    "matematik:2": "d675e0e419d3597ece0c9e3340fcbdb1f787535988a4912fda8f00c90b8bccf6",
    "matematik:3": "07a383d5c1f2560093f808affc9770081cb539d026230918d22623fcef0bd88b"
}

def enabled():
    return os.environ.get("CIKGULAJU_RPT_NATIVE_WORD_BATCH") == "1"

def eligible(subject,year,source,*,root):
    if not enabled() or source is None:
        return False
    digest=PINS.get(f"{subject}:{year}")
    if not digest:
        return False
    try:
        base=Path(root)/"web_2027_pdfs"
        source=Path(source)
        if source != base/subject/f"tahun_{year}.pdf" or source.is_symlink():
            return False
        if not 8000<=source.stat().st_size<=25*1024*1024:
            return False
        return hashlib.sha256(source.read_bytes()).hexdigest()==digest
    except OSError:
        return False

def document(subject,year,source,account,config,*,root):
    from web.english_rpt_2027_http import _has_paid_access
    if not _has_paid_access(account):
        raise PermissionError("Paid RPT Word only")
    if not eligible(subject,year,source,root=root):
        raise ValueError("RPT source not approved for this batch")
    from tools.build_kssr_rpt_merged_week_batch_20261126 import build_word
    from web.rpt_native_word_cover import personalized_word
    base=Path(root)/"web_2027_pdfs"
    manifest=json.loads((base/"manifest.json").read_text("utf-8"))
    lock=json.loads((base/"original_cover_layout_verified.json").read_text("utf-8"))
    blob,raw,actual,*_=build_word(subject,year,manifest,lock,root=base)
    if actual!=Path(source) or hashlib.sha256(raw).hexdigest()!=PINS[f"{subject}:{year}"]:
        raise ValueError("RPT source changed")
    result=personalized_word(blob,raw,lock,f"{subject}:{year}",account,config)
    return result,hashlib.sha256(result).hexdigest()

APPROVED_SCIENCE_PINS={
    5:"281d25b8b37cfda50caa22ebcc9ee235767e1bfb4a8a4cfad171a5bf324a1e8b",
    6:"0f168595c8c6259c455f143aeeb98489152a85cc599e5c1d60db88d19503d477",
}

def eligible_approved_science(year,source,*,root):
    if not enabled() or year not in APPROVED_SCIENCE_PINS or source is None:
        return False
    from rpt_2027.sains import sk_documents
    try:
        expected=sk_documents.document_path(year,root=Path(root)/"sains")
        return (expected is not None and Path(source)==expected and
                hashlib.sha256(expected.read_bytes()).hexdigest()==APPROVED_SCIENCE_PINS[year])
    except OSError:
        return False

def approved_science_document(year,source,account,config,*,root):
    from web.english_rpt_2027_http import _has_paid_access
    if not _has_paid_access(account):
        raise PermissionError("Paid RPT Word only")
    if not eligible_approved_science(year,source,root=root):
        raise ValueError("Approved Science PDF changed")
    from tools.build_rpt_science_approved_word_20261126 import build_word
    from web.rpt_native_word_cover import personalized_word
    blob,raw,*_=build_word(year,root=root)
    if hashlib.sha256(raw).hexdigest()!=APPROVED_SCIENCE_PINS[year]:
        raise ValueError("Approved Science source changed")
    lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))
    result=personalized_word(blob,raw,lock,f"sains:{year}",account,config)
    return result,hashlib.sha256(result).hexdigest()

def eligible_approved_math(year,source,*,root):
    if not enabled() or source is None:
        return False
    from rpt_2027.matematik import sk_documents
    try:
        expected=sk_documents.document_path(year,root=Path(root)/"matematik")
        return (year in sk_documents.DIGESTS and expected is not None and Path(source)==expected
                and hashlib.sha256(expected.read_bytes()).hexdigest()==sk_documents.DIGESTS[year])
    except OSError:
        return False

def approved_math_document(year,source,account,config,*,root):
    from web.english_rpt_2027_http import _has_paid_access
    if not _has_paid_access(account):
        raise PermissionError("Paid RPT Word only")
    if not eligible_approved_math(year,source,root=root):
        raise ValueError("Approved Math PDF changed")
    from rpt_2027.matematik import sk_documents
    from tools.build_rpt_math_upper_native_word_20261126 import build_word
    from web.rpt_native_word_cover import personalized_word
    blob,raw,*_=build_word(year,root=root)
    if hashlib.sha256(raw).hexdigest()!=sk_documents.DIGESTS[year]:
        raise ValueError("Approved Math source changed")
    lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))
    result=personalized_word(blob,raw,lock,f"matematik:{year}",account,config)
    return result,hashlib.sha256(result).hexdigest()

def eligible_integrated_english(year,source,source_digest,*,root):
    if not enabled() or source is None or year not in range(2,7):
        return False
    try:
        lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))
        digest=lock["english_integrated"]["source_sha256_by_subject_year"][f"english:{year}"]
        expected=Path(root)/"english"/f"RPT_English_SK_2027_Year_{year}_A_B.pdf"
        return (Path(source)==expected and not expected.is_symlink() and source_digest==digest
                and hashlib.sha256(expected.read_bytes()).hexdigest()==digest)
    except (OSError,ValueError,KeyError,TypeError):
        return False

def integrated_english_document(year,source,source_digest,account,config,*,root):
    from web.english_rpt_2027_http import _has_paid_access
    if not _has_paid_access(account):
        raise PermissionError("Paid RPT Word only")
    if not eligible_integrated_english(year,source,source_digest,root=root):
        raise ValueError("Integrated English source changed")
    from tools.build_english_rpt_merged_week_word_pdf_20261126 import build_word
    from web.rpt_native_word_cover import personalized_word
    blob,raw,actual,digest=build_word(year)
    if actual.resolve()!=Path(source).resolve() or digest!=source_digest or hashlib.sha256(raw).hexdigest()!=digest:
        raise ValueError("Integrated English source changed")
    lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))
    result=personalized_word(blob,raw,lock,f"english:{year}",account,config)
    return result,hashlib.sha256(result).hexdigest()

def eligible_dlp(subject,year,*,root):
    if not enabled():
        return False
    from rpt_2027.dlp.documents import document_path
    from tools.build_rpt_dlp_native_20261126 import PINS as dlp_pins
    try:
        expected=dlp_pins.get(f"{subject}:{year}")
        path=document_path(subject,year,root=Path(root)/"dlp")
        return bool(expected and path and hashlib.sha256(path.read_bytes()).hexdigest()==expected)
    except OSError:
        return False

def dlp_document(subject,year,account,config,*,root):
    from web.english_rpt_2027_http import _has_paid_access
    if not _has_paid_access(account):
        raise PermissionError("Paid RPT Word only")
    if not eligible_dlp(subject,year,root=root):
        raise ValueError("DLP RPT source changed")
    from tools.build_rpt_dlp_native_20261126 import build_word,PINS as dlp_pins
    from web.rpt_native_word_cover import personalized_word
    from web.rpt_compact_pdf import read_full_standards_dlp
    from rpt_2027.dlp.documents import document_path
    original=document_path(subject,year,root=Path(root)/"dlp").read_bytes()
    key=f"{subject}:{year}"
    revised=read_full_standards_dlp(subject,year,original,root=root)
    if revised is not None:
        from tools.build_rpt_dlp_full_standards_20261126 import build_word as build_revised
        blob,_,_,_,_=build_revised(subject,year,root=root)
        pdf_bytes,_=revised
        lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))
        result=personalized_word(blob,pdf_bytes,lock,key,account,config)
        return result,hashlib.sha256(result).hexdigest()
    blob,raw,_=build_word(subject,year,root=root)
    if hashlib.sha256(raw).hexdigest()!=dlp_pins[key]:
        raise ValueError("DLP RPT source changed")
    lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text("utf8"))
    result=personalized_word(blob,raw,lock,key,account,config)
    return result,hashlib.sha256(result).hexdigest()
