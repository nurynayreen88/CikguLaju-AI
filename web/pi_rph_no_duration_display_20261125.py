"""Remove PI scheduling annotations from display titles only.
Keep lesson content, actual teacher-entered time, source keys and Tasmik label.
"""
import re
from functools import wraps
from web.rph_pi_jawi_numerals_20261124 import is_active_pi_rph

# Explicit schedule tokens in a topic/title field, never activity instructions.
_DURATION=r"\d{1,3}[ \t]*(?:jam|minit|hours?|minutes?|جم|مينيت|مينت)"
_PAREN=re.compile(rf"[ \t]*\([ \t]*{_DURATION}[ \t]*\)",re.I)
_BARE=re.compile(rf"(?<![\w\d]){_DURATION}(?![\w\d])",re.I)

def display_topic(value):
    if not isinstance(value,str):
        return value
    revised=_BARE.sub("",_PAREN.sub("",value))
    if revised==value:
        return value
    revised=re.sub(r"[ \t]{2,}"," ",revised).strip()
    revised=re.sub(r"[ \t]*\+[ \t]*$","",revised).strip()
    return revised

def display_state(state):
    if not is_active_pi_rph(state):
        return state
    updated=dict(state)
    for key in ("topic","subtopic"):
        if key in state:
            updated[key]=display_topic(state[key])
    return updated

def display_rows(state,rows):
    if not is_active_pi_rph(state) or not isinstance(rows,dict):
        return rows
    updated=dict(rows)
    for key in ("TAJUK","TOPIC","SUBTOPIK","SUBTOPIC"):
        if key in rows:
            updated[key]=display_topic(rows[key])
    return updated

def install(runtime):
    if getattr(runtime,"_PI_DISPLAY_NO_DURATION",False):
        return True
    old=getattr(runtime,"_rph_rows",None)
    if not callable(old):
        return False
    @wraps(old)
    def rows(state,*args,**kwargs):
        return display_rows(state,old(state,*args,**kwargs))
    runtime._rph_rows=rows
    renderer=getattr(runtime,"_create_rph_word",None)
    globals_=getattr(renderer,"__globals__",None)
    if isinstance(globals_,dict) and globals_ is not vars(runtime) and globals_.get("_rph_rows") is old:
        globals_["_rph_rows"]=rows
    for name in ("create_word_file","create_pdf_file"):
        previous=getattr(runtime,name,None)
        if callable(previous):
            def make_wrapper(fn):
                @wraps(fn)
                def wrapped(state,*args,**kwargs):
                    return fn(display_state(state),*args,**kwargs)
                return wrapped
            setattr(runtime,name,make_wrapper(previous))
    runtime._PI_DISPLAY_NO_DURATION=True
    return True
