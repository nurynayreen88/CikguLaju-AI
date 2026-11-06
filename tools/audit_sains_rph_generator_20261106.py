"""Static scanner for all native RPH text generator branches. No bot import."""
import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"app.py").read_text("utf-8")
tree=ast.parse(source)
target={"_local_rph_text","_sm2542_rows","_rph_template","_rph_activity"}
sections=[]
for n in ast.walk(tree):
    if not isinstance(n,ast.FunctionDef):
        continue
    src=ast.get_source_segment(source,n) or ""
    low=(src[:1200] if n.name=="_local_rph_text" else src).lower()
    if n.name!="_local_rph_text" and not ("sains" in low and ("rph" in n.name or "pdp" in n.name)):
        continue
    if n.name=="_local_rph_text":
        sections.append({"function":n.name,"line":n.lineno,"length":len(src),
            "body_begin":src[:6500] if len(src)<6500 else src[:4000],
            "science_mentions":[line.strip()[:180] for line in src.splitlines() if "sains" in line.lower()][:15]})
    else:
        sections.append({"function":n.name,"line":n.lineno,"length":len(src),"body_begin":src[:750]})
print(json.dumps(sections,ensure_ascii=False,indent=2))
