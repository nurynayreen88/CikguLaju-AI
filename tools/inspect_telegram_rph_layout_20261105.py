from pathlib import Path
lines=Path("app.py").read_text("utf8").splitlines()
for start,end in ((10190,10227),(10124,10138),(3188,3201)):
 print("SECTION",start,end)
 for i in range(start-1,end):
  print(f"{i+1}: {lines[i]}")
