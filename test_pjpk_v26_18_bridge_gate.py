"""Isolated bridge-gate test: extracts only v26.18 AST nodes; does not import app.py."""
import ast
import os
from pathlib import Path
import pjpk_t3_safe_preview_adapter as adapter

root = Path(__file__).resolve().parent
tree = ast.parse((root / "app.py").read_text(encoding="utf-8-sig"))
names = {"CIKGULAJU_PJPK_T3_EDITORIAL_BRIDGE_ENABLED", "CIKGULAJU_PJPK_T3_EDITORIAL_BRIDGE_ERROR"}
functions = {"cikgulaju_pjpk_t3_editorial_preview", "cikgulaju_pjpk_t3_editorial_options"}
selected = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
        selected.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in functions:
        selected.append(node)
    elif isinstance(node, ast.Try) and any(isinstance(n, ast.Name) and n.id == "CIKGULAJU_PJPK_T3_EDITORIAL_BRIDGE_ENABLED" for n in ast.walk(node)):
        # The final bridge initializer, not unrelated app try blocks.
        if getattr(node, "lineno", 0) > next(n.lineno for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "cikgulaju_pjpk_t3_editorial_options"):
            selected.append(node)
assert len(selected) == 5, [type(n).__name__ for n in selected]
code = compile(ast.Module(body=selected, type_ignores=[]), str(root / "app.py"), "exec")
old = {k: os.environ.get(k) for k in ("CIKGULAJU_PJPK_T3_EDITORIAL_PREVIEW", "CIKGULAJU_PJPK_T3_CANDIDATE_DB")}
def load(flag, db):
    os.environ["CIKGULAJU_PJPK_T3_EDITORIAL_PREVIEW"] = flag
    os.environ["CIKGULAJU_PJPK_T3_CANDIDATE_DB"] = str(db)
    ns = {"os": os}
    exec(code, ns)
    return ns
try:
    n = load("0", root / "pjpk_candidate.db")
    assert not n["CIKGULAJU_PJPK_T3_EDITORIAL_BRIDGE_ENABLED"]
    assert n["cikgulaju_pjpk_t3_editorial_options"]("PJ") == []
    try: n["cikgulaju_pjpk_t3_editorial_preview"]("PJ", "2")
    except ValueError: pass
    else: raise AssertionError("OFF gate bypass")
    n = load("1", root / "__missing_candidate.db")
    assert not n["CIKGULAJU_PJPK_T3_EDITORIAL_BRIDGE_ENABLED"]
    n = load("1", root / "pjpk_candidate.db")
    assert n["CIKGULAJU_PJPK_T3_EDITORIAL_BRIDGE_ENABLED"], n["CIKGULAJU_PJPK_T3_EDITORIAL_BRIDGE_ERROR"]
    assert len(n["cikgulaju_pjpk_t3_editorial_options"]("PJ")) == 33
    assert len(n["cikgulaju_pjpk_t3_editorial_options"]("PK")) == 10
    assert n["cikgulaju_pjpk_t3_editorial_preview"]("PJ", "2")["production_allowed"] is False
    try: n["cikgulaju_pjpk_t3_editorial_preview"]("PJ", "2", mode="production")
    except ValueError: pass
    else: raise AssertionError("Production gate bypass")
    print("PASS: OFF, missing DB fail-closed, ON 43 options, production blocked")
finally:
    for k,v in old.items():
        if v is None: os.environ.pop(k, None)
        else: os.environ[k] = v
