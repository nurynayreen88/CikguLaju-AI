"""Inspect final native RPH generator text without importing Telegram."""
from __future__ import annotations
import ast, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    src=(ROOT/"app.py").read_text("utf-8")
    tree=ast.parse(src)
    defs=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
          and n.name in ("_local_rph_text","create_word_file","create_pdf_file")]
    out={}
    for name in ("_local_rph_text","create_word_file","create_pdf_file"):
        selected=[n for n in defs if n.name==name]
        if not selected:
            out[name]={"found":False};continue
        last=max(selected,key=lambda n:n.lineno)
        body=ast.get_source_segment(src,last) or ""
        out[name]={
            "found":True,
            "definitions":len(selected),
            "last_start_line":last.lineno,
            "last_end_line":last.end_lineno,
            "last_own_science_reference":"sains" in body.lower(),
            "last_body_excerpt":body[:11500] if name=="_local_rph_text" else body[:3500],
        }
    print(json.dumps({"source":"static app AST, no bot import","functions":out},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
