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
    for node in tree.body:
        if isinstance(node, ast.Assign):
            # Track aliases in exact execution order, not after all class
            # definitions: a base can be assigned between two overrides.
            if isinstance(node.value, ast.Name) and node.value.id in seen:
                seen.update(t.id for t in node.targets if isinstance(t,ast.Name))
        elif isinstance(node, ast.ClassDef) and node.name==TARGET:
            for base in node.bases:
                name=ast.unparse(base)
                if name not in seen:
                    raise ValueError(f"Unknown renderer base at line {node.lineno}: {name}")
            seen.add(TARGET)
    return {"class_definitions":len(versions),"versions":versions,"aliases":aliases}

if __name__=="__main__":
    print(json.dumps(inspect(SOURCE.read_text(encoding="utf-8")),indent=2))
