"""Inspect Telegram's actual RPH document layout and upstream generator only.

No execution/import of app.py, no tokens/secrets or DB access. Print structural
signatures plus shortened static sections for accurate Web parity.
"""
import ast
from pathlib import Path
source=Path("app.py").read_text("utf8")
lines=source.splitlines()
tree=ast.parse(source)
targets=[]
for node in ast.walk(tree):
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
        name=node.name
        start=node.lineno
        end=getattr(node,"end_lineno",start)
        snippet="\n".join(lines[start-1:end])
        needles=(
           "Document(", ".add_table(", "Table(", "_rph_rows", "_rph_doc",
           "_rph_pdf", "RANCANGAN PENGAJARAN HARIAN", "font.size",
           "add_cell(", "set_cell(", "set_col_width", "docx",
           "render_rph", "make_rph", "pdf_rph", "word_rph"
        )
        score=sum(k.lower() in snippet.lower() for k in needles)
        if score>=3 or any(k in name.lower() for k in ("rph_rows","generate_rph","rph_word","rph_docx","rph_pdf")):
            targets.append((start,end,name,score))
for n,(start,end,name,score) in enumerate(sorted(targets,key=lambda t:(-t[3],t[0]))[:90]):
 print("FUNC",start,end,name,"score",score,"length",end-start+1)
 if score>=5 and end-start<420 and (not name.startswith("test_")):
  print("SECTION",name)
  for k in range(start-1,end):
   line=lines[k]
   if any(x in line.upper() for x in ("TOKEN=", "SECRET=", "API_KEY=", "BOT_TOKEN", "PASSWORD=")):
    print(k+1,"[REDACTED]");continue
   print(f"{k+1:05d} {line[:205]}")
