"""Read-only static search for English Year3 Lesson 93 audio route in app.py.

Do not import the production application, access user/credit data or send media.
An absence of a literal route does not establish absent audio; it may live in
the currently active curriculum database and needs separate authenticated QA.
"""
import ast,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NAME=re.compile(r"(?i)(?:^_?en3|^_?eng3|english.?y3|year.?3)")
KEY=re.compile(r"(?i)^\s*(?:0*93|lesson.?0*93)\s*$")

def _targets(n):
    if not isinstance(n,(ast.Assign,ast.AnnAssign)):
        return []
    targets=n.targets if isinstance(n,ast.Assign) else [n.target]
    return [t.id for t in targets if isinstance(t,ast.Name)]

def run():
    tree=ast.parse((ROOT/"app.py").read_text(encoding="utf-8"))
    relevant=[]
    for node in tree.body:
        names=_targets(node)
        if not any(NAME.search(name) for name in names):
            continue
        value=getattr(node,"value",None)
        if not isinstance(value,ast.Dict):
            continue
        hits=[]
        for key,val in zip(value.keys,value.values):
            if isinstance(key,ast.Constant) and KEY.match(str(key.value)):
                try:
                    row=ast.literal_eval(val)
                    if isinstance(row,list):
                        rows=[{"label":str(x.get("audio_reference") or "")[:90],
                               "has_drive_id":bool(x.get("storage_file_id")),
                               "verified_flag":bool(x.get("verified"))}
                              for x in row if isinstance(x,dict)]
                    elif isinstance(row,dict):
                        rows=[{"label":str(row.get("audio_reference") or "")[:90],
                               "has_drive_id":bool(row.get("storage_file_id")),
                               "verified_flag":bool(row.get("verified"))}]
                    else:
                        rows=[{"value_type":type(row).__name__}]
                    hits.extend(rows)
                except (ValueError,TypeError,MemoryError,RecursionError):
                    hits.append({"status":"NOT_STATIC_LITERAL"})
        if hits:
            relevant.append({"name":names,"line":node.lineno,"lesson_93_rows":hits})
    functions=[{"name":fn.name,"line":fn.lineno}
               for fn in tree.body if isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef))
               and re.search(r"(?i)(?:en3|eng3|english.y3|year.?3)",fn.name)]
    report={
        "scope":"top-level year3/audio literal dictionaries in current app.py only",
        "lesson93_literal_matches":relevant[:30],
        "other_year3_function_count":len(functions),
        "other_year3_functions":functions[:35],
        "source_tb_track97_verified":True,
        "source_tb_cd1_verified":False,
        "actual_media_file_id_verified":False,
        "live_telegram_send_verified":False,
        "interpretation":"Only genuine Year3-specific top-level dictionary names were checked; Year4 maps must never count as Year3 evidence. Any missing Year3 audio source may be stored in a separate curriculum DB or indirect runtime route.",
        "release_status":"NO_FINAL_READY",
    }
    print("YEAR3_LESSON93_AUDIO_STATIC_ROUTE_SEARCH",json.dumps(report,sort_keys=True))
    return report

if __name__=="__main__":
    run()
