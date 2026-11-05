"""Temporary static audit of Telegram profile/schedule paths; no secrets or user data."""
import ast
from pathlib import Path

path=Path("app.py")
code=path.read_text("utf-8")
lines=code.splitlines()
print("APP_LINES",len(lines),"APP_BYTES",len(code.encode("utf-8")))
tree=ast.parse(code)
functions=[]
for node in ast.walk(tree):
 if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
  functions.append((node.lineno,node.name,",".join(a.arg for a in node.args.args)))
for n,name,args in sorted(functions):
 if any(x in name.lower() for x in ("profile","teacher","timetable","jadual","class","state","register","text","callback","webhook","send","message","menu","save")):
  print("DEF",n,name,"("+args[:100]+")")
patterns=[
 "Profil Saya","Jadual Waktu","jadual waktu","teacher_profiles",
 "class_names","class_profiles","school_name","display_name",
 "nama kelas","Nama Kelas","nama sekolah","Nama Sekolah",
 "save_profile","time_table","schedule","timetable","_sb_request",
 "def callback","def send","def handle_","@app.route","@app.post"
]
for key in patterns:
 hits=[i for i,line in enumerate(lines) if key.lower() in line.lower()]
 print("PATTERN",repr(key),"COUNT",len(hits),"LINES",[i+1 for i in hits[:45]])
 for i in hits[:8]:
  lo=max(0,i-5); hi=min(len(lines),i+8)
  # Never print actual user/bot tokens or endpoint URLs in source.
  for k in range(lo,hi):
   raw=lines[k]
   if any(q in raw.lower() for q in ("token=", "secret=", "api_key", "password=", "bot_token")): continue
   print(f" {k+1:05d} {raw[:210]}")
