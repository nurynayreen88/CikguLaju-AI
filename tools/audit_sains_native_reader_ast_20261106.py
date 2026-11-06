"""Static, read-only AST inventory of Telegram's native Sains sequence reader.

Does not import app.py (which may initialize the bot), open credentials,
or execute database queries. Prints only relevant function names, calls and
short SQL/path literals. This is diagnostic evidence, not runtime signoff.
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = {
    "_sm2542_rows", "_sm2542_unique_units",
    "_sm2542_grouped_pdps", "_sm2542_pdp_options",
}


def main():
    tree = ast.parse((ROOT / "app.py").read_text("utf-8"), filename="app.py")
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name not in NAMES:
            continue
        calls = set()
        literals = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                name = sub.func
                if isinstance(name, ast.Name):
                    calls.add(name.id)
                elif isinstance(name, ast.Attribute):
                    calls.add(name.attr)
            elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                t = sub.value.strip()
                if any(token in t.lower() for token in (
                    "pdp_sequence", "rpt_entries", "sains", "science",
                    "db_path", "v25_68", "v26_00"
                )):
                    literals.add(t[:450])
        found.append({
            "function": node.name,
            "first_line": node.lineno,
            "last_line": node.end_lineno,
            "calls": sorted(calls)[:100],
            "source_literals": sorted(literals)[:35],
        })
    print(json.dumps({"source": "app.py AST (not imported)",
                      "found": found,
                      "required_native_reader_present": any(
                          f["function"] == "_sm2542_rows" for f in found)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
