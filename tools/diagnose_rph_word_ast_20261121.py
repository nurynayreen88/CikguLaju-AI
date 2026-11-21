"""Read-only report of active-vs-frozen Word builder changes (no approval bypass).

This is an audit aid: every changed function needs actual layout review and A4
verification before updating the frozen QA snapshot or merging style changes.
"""
import ast
from difflib import unified_diff
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("_rph_document_rows", "_rph_table_labels", "_create_rph_word")


def _active(app, name):
    start = app.rindex("\ndef " + name + "(") + 1
    body = app.index("\n", start) + 1
    end_match = re.search(r"(?m)^def ", app[body:])
    end = body + end_match.start() if end_match else len(app)
    return ast.parse(app[start:end]).body[0]


def main():
    app = (ROOT / "app.py").read_text("utf-8")
    frozen = (ROOT / "qa/english_word_builder_snapshot.py").read_text("utf-8")
    snapshots = {
        n.name: n for n in ast.parse(frozen).body if isinstance(n, ast.FunctionDef)
    }
    changed = 0
    for name in NAMES:
        active_node = _active(app, name)
        saved_node = snapshots[name]
        if ast.dump(active_node, include_attributes=False) == ast.dump(saved_node, include_attributes=False):
            print("AST MATCH:", name)
            continue
        changed += 1
        # Display a bounded, human-readable diagnostic only; do not silently
        # rebaseline snapshots or change runtime behavior.
        old = ast.unparse(saved_node).splitlines()
        new = ast.unparse(active_node).splitlines()
        diff = list(unified_diff(old, new, fromfile="frozen/"+name,
                                 tofile="active/"+name, lineterm=""))
        print("AST DIFF:", name, "lines:", len(diff))
        print("\n".join(diff[:240]))
        if len(diff) > 240:
            print("TRUNCATED DIFF; REVIEW FULL ACTUAL SOURCE BEFORE SNAPSHOT UPDATE")
    print("AST FUNCTIONS CHANGED:", changed)
    # Diagnostic exits successfully even with differences. The strict
    # validate_word_function_snapshot() gate remains unchanged and blocking.
    return changed


if __name__ == "__main__":
    main()
