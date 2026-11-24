"""Final native SK RPH standard cell line breaks; source identities stay intact."""
import re
from functools import wraps

SUBJECTS = frozenset(("bahasa melayu", "matematik", "sains",
    "english", "bahasa inggeris", "pendidikan jasmani",
    "pendidikan kesihatan", "pendidikan jasmani dan pendidikan kesihatan",
    "pendidikan seni visual", "reka bentuk dan teknologi", "sejarah",
    "pendidikan muzik", "pendidikan moral"))
# Exact numeric DSKP codes, including Math subclauses. Only a known source
# join separator followed by a full code is a break, not prose punctuation.
CODE = r"\d+(?:\.\d+){1,3}(?:\([ivxlcdm]+\))?"
BOUNDARY = re.compile(r"[ \t]*(?:[;|·])[ \t]*(?="+CODE+r"(?![\d.(])(?:\s|$))", re.I)
START = re.compile(r"^"+CODE+r"(?![\d.(])(?:\s|$)",re.I)
MARKER = "_CIKGULAJU_STANDARD_ONE_CODE_PER_LINE_20261124"

def standard_lines(value):
    if not isinstance(value,str) or not START.match(value.strip()):
        return value
    return BOUNDARY.sub("\n",value)

def display_rows(state,rows):
    if not isinstance(state,dict) or not isinstance(rows,dict):
        return rows
    if str(state.get("task","")).strip().casefold()!="rph":
        return rows
    if str(state.get("subject","")).strip().casefold() not in SUBJECTS:
        return rows
    if any(token in str(state.get(key,"")).casefold()
           for key in ("curriculum","curriculum_version","stream","programme","program","school_type")
           for token in ("dlp","ppki","sjkc","sjkt","kp2027")):
        return rows
    changes={}
    for key in ("STANDARD KANDUNGAN","STANDARD PEMBELAJARAN",
                "MAIN CONTENT STANDARD","MAIN LEARNING STANDARD",
                "COMPLEMENTARY CONTENT STANDARD","COMPLEMENTARY LEARNING STANDARD"):
        old=rows.get(key)
        new=standard_lines(old)
        if new!=old:
            changes[key]=new
    return {**rows,**changes} if changes else rows

def install(runtime):
    if getattr(runtime,MARKER,False):
        return True
    previous=getattr(runtime,"_rph_rows",None)
    if not callable(previous):
        return False
    @wraps(previous)
    def rows(state,*args,**kwargs):
        return display_rows(state,previous(state,*args,**kwargs))
    runtime._rph_rows=rows
    setattr(runtime,MARKER,True)
    return True
