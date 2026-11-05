"""Read-only inventory of actual Telegram audio send functions in app.py.

Do not import app.py or inspect users/credentials. Never transmit media.
This audit intentionally captures only function names, line numbers, and
known call-method names so WMA can be preserved without blind format edits.
"""
import ast
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("media", "audio", "reference_material", "verified_media")

def _name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _name(node.value) + "." + node.attr
    return ""

def run():
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(k in node.name.lower() for k in KEYS):
            continue
        calls = sorted({s for call in ast.walk(node) if isinstance(call, ast.Call)
                        if (s := _name(call.func)) and
                        any(word in s.lower() for word in
                            ("send", "download", "request", "document", "audio", "mime", "file"))})
        if not calls and "media" not in node.name.lower():
            continue
        found.append({
            "name": node.name,
            "lineno": node.lineno,
            "call_names": calls[:35],
        })
    report = {
        "scope": "AST metadata only: app.py send functions, no file download or Telegram transmission",
        "functions": sorted(found, key=lambda x: x["lineno"]),
        "wma_policy": "Keep source .wma bytes and extension. No forced .mp3 label or audio/mpeg. Block wrong textbook provenance regardless of extension.",
        "verification": "CODE_PATH_INVENTORY_ONLY_NOT_REAL_SEND",
    }
    print("CIKGULAJU_WMA_SENDER_STATIC_AUDIT", json.dumps(report, ensure_ascii=False))
    return report

if __name__ == "__main__":
    run()
