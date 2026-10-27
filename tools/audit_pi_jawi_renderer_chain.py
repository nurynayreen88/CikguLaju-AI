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
    # A final class can silently lose methods if an intermediate override is
    # bypassed. Record the complete class lineage rather than treating the
    # isolated first/last Flowable PDF as production evidence.
    # Verify every successive class is connected to its immediate predecessor.
    # A saved alias between class declarations is the only safe handoff.
    if len(versions) > 1:
        for earlier, later in zip(versions, versions[1:]):
            handoffs = [a for a in aliases
                        if earlier["line"] < a["line"] < later["line"]
                        and a["value"] == TARGET]
            allowed = {name for a in handoffs for name in a["aliases"]}
            if len(later["bases"]) != 1 or later["bases"][0] not in allowed:
                raise ValueError(
                    f"Renderer override at line {later['line']} skips "
                    f"previous definition at line {earlier['line']}"
                )
    if len(versions) > 2:
        # The final implementation must inherit from an alias saved from the
        # immediately preceding definition; otherwise overrides are skipped.
        previous = versions[-2]["line"]
        last = versions[-1]
        final_base = last["bases"][0] if len(last["bases"]) == 1 else None
        final_aliases = [a for a in aliases if previous < a["line"] < last["line"]
                         and a["value"] == TARGET]
        if final_base not in [name for a in final_aliases for name in a["aliases"]]:
            raise ValueError("Final renderer does not inherit the preceding saved implementation")
        print("WARNING: isolated first/last Flowable smoke test omits "
              f"{len(versions)-2} intermediate renderer definitions; "
              "production PDF rendering remains unverified.")
    # Surface the exact helper calls made by the final implementation so
    # the next production-equivalent harness can load those dependencies.
    final_node = next(node for node in reversed(tree.body)
                      if isinstance(node, ast.ClassDef) and node.name == TARGET)
    final_helpers = sorted({
        n.func.id for n in ast.walk(final_node)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id.startswith("_")
    })
    return {"class_definitions":len(versions),"versions":versions,
            "aliases":aliases,"final_renderer_helper_calls":final_helpers}


if __name__=="__main__":
    print(json.dumps(inspect(SOURCE.read_text(encoding="utf-8")),indent=2))
