"""Science Y4/5 optional 60-minute delivery; keep original source plans intact."""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import json,re,os
@lru_cache(maxsize=1)
def _data():
    return json.loads(Path(__file__).with_name("science_y45_session_reinforcement.json").read_text())["sets"]

def active():
    return os.getenv("CIKGULAJU_DLP_SCIENCE_Y45_SESSION","")=="1"

def extend(plan,year,*,force=False):
    if not force and not active():return plan
    if year not in (4,5) or plan["minutes"]!=30:return plan
    key=plan["id"].split("-")[-1]
    item=_data()[f"science_dlp:{year}"].get(key)
    assert item is not None,(year,key)
    p=deepcopy(plan)
    if year==4:
        p["phases"].insert(-2,deepcopy(item))
    else:
        p["phases"].insert(-2,(f"{item['phase']} · 30 min",item["teacher"],item["pupils"]))
        p["label"]=re.sub(r"30 min$", "60 min",p["label"])
    p["minutes"]=60
    p["materials"]+="; activity-specific cards, diagrams or recorded results as described in targeted reinforcement"
    return p

def for_teacher(original,year,teacher):
    # If a teacher actually has a 30-minute slot, never squeeze 60 minutes
    # of activities into it. Existing source RPH remains available unchanged.
    time=(teacher or {}).get("time") or ""
    m=re.fullmatch(r"\s*(\d\d):(\d\d)\s*[-–—]\s*(\d\d):(\d\d)\s*",time)
    if m:
        a,b,c,d=map(int,m.groups())
        if (c*60+d)-(a*60+b)<60:return original
    return extend(original,year)
