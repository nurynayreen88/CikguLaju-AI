"""Audit the real ordered Jawi renderer override chain without importing app.py.

Read-only; useful because app.py contains many redefinitions of the same class.
"""
import ast
import json
from pathlib import Path

SOURCE=Path("app.py")
TARGET="_JawiRasterParagraph_v25213"

def inspect(source):
    tree=ast.parse(source)
    versions=[]
    aliases=[]
    for node in tree.body:
        if isinstance(node,ast.ClassDef) and node.name==TARGET:
            versions.append({"line":node.lineno,"bases":[ast.unparse(x) for x in node.bases],
                             "methods":[x.name for x in node.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]})
        elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id.startswith("_JawiRasterParagraph_") for t in node.targets):
            names=[t.id for t in node.targets if isinstance(t,ast.Name)]
            if TARGET in ast.unparse(node.value):
                aliases.append({"line":node.lineno,"aliases":names,"value":ast.unparse(node.value)})
    if not versions:
        raise ValueError("No Jawi renderer class found")
    # Each override must use either the original Flowable or a previously saved
    # class alias; otherwise it silently discards previous behavior.
    seen={"Flowable"}
    for v in versions:
        for base in v["bases"]:
            if base not in seen:
                raise ValueError(f"Unknown renderer base at line {v['line']}: {base}")
        for a in aliases:
            if a["line"]>v["line"]: continue
            if a["value"]==TARGET: seen.update(a["aliases"])
    return {"class_definitions":len(versions),"versions":versions,"aliases":aliases}

if __name__=="__main__":
    print(json.dumps(inspect(SOURCE.read_text(encoding="utf-8")),indent=2))
