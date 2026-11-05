"""Static audit: native Telegram document entrypoints, parser, RPH metadata."""
from pathlib import Path
import ast
text=Path("app.py").read_text("utf8")
lines=text.splitlines()
tree=ast.parse(text)
targets=["_parse_rph_sections","_rph_rows","_rph_session_meta","_create_rph_word",
         "create_word_file","create_pdf_file","_rph_format_activity_lines"]
found={}
for node in ast.walk(tree):
 if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in targets:
  found.setdefault(node.name,[]).append(node)
for name in targets:
 rows=found.get(name,[])
 print("NAME",name,"COUNT",len(rows))
 for node in rows[-2:]:
  print("METHOD",name,"start",node.lineno,"end",node.end_lineno)
  if name=="create_pdf_file":
   for k in range(node.lineno-1,min(node.lineno+30,node.end_lineno)):
    print(f"{k+1}: {lines[k][:250]}")
  elif node.end_lineno-node.lineno<140:
   for k in range(node.lineno-1,node.end_lineno):
    print(f"{k+1}: {lines[k][:250]}")
