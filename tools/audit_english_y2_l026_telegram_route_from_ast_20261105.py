"""Read-only check of *actual* English Year1/2 Telegram WMA route literals.

Uses AST to avoid importing the multi-megabyte production Flask/Telegram app.
Only prints the two Year2 Lesson26 source file IDs and whether they match
original Drive assets; never reads user data or sends Telegram requests.
"""
import ast
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
EXPECTED={
    "CD2-35":"1ZxYROG_L291L8WWIq2_J3NZDiW8giBkK",
    "CD2-36":"1DZnb_IvBrqYfNZqWxuliQlJ-uGPgqIz9",
}

def extract():
    source=(ROOT/"app.py").read_text(encoding="utf-8")
    tree=ast.parse(source)
    functions=[fn for fn in tree.body if isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef))
               and fn.name=="_eng12_send_verified_audio"]
    if not functions:
        raise RuntimeError("Year1/Year2 audio sender absent in actual app.py")
    fn=functions[-1]
    mapping=[]
    for node in ast.walk(fn):
        if not isinstance(node,ast.Assign):
            continue
        if any(isinstance(target,ast.Name) and target.id=="drive_files" for target in node.targets):
            try:
                data=ast.literal_eval(node.value)
            except (ValueError,TypeError,RecursionError):
                continue
            if isinstance(data,dict):
                mapping.append(data)
    if len(mapping)!=1:
        raise RuntimeError("Expected one literal drive_files map in Year1/Year2 sender; got "+str(len(mapping)))
    return mapping[0], fn.lineno

def run():
    mapping,line=extract()
    relevant={}
    for name,expected_id in EXPECTED.items():
        disc,track=map(int,re.search(r"CD([123])-(\d{1,3})",name).groups())
        matching=[(str(key),str(fid)) for key,fid in mapping.items()
                  if (lambda m: m and int(m.group(1))==disc and int(m.group(2))==track)
                     (re.search(r"(?i)(?:CD)?\s*([123])\s*[-_ ]\s*0*(\d{1,3})\b",str(key)))]
        relevant[name]={
            "matches":matching,
            "expected_drive_id":expected_id,
            "route_id_matches_original":len(matching)==1 and matching[0][1]==expected_id,
            "route_provenance":"CODE_LITERAL_ONLY_NOT_RUNTIME_SEND",
        }
    report={"sender":"_eng12_send_verified_audio","source_line":line,
            "audio_total_literal_entries":len(mapping),"target_routes":relevant,
            "telegram_delivery_verified":False,"spoken_audio_verified":False}
    print("ENGLISH_Y2_L026_ACTUAL_BOT_WMA_ROUTE_AUDIT",json.dumps(report,sort_keys=True))
    return report

if __name__=="__main__":
    run()
