"""Static review of webhook and text dispatch for an isolated school edit."""
from pathlib import Path
lines=Path("app.py").read_text("utf-8").splitlines()
for start,end in ((15999,16096),(37774,37843),(6320,6395),
                  (39610,39665),(12690,12780)):
 print("SECTION",start,end)
 for i in range(start-1,min(end,len(lines))):
  line=lines[i]
  if any(w in line.upper() for w in ("TOKEN=", "SECRET=", "API_KEY=", "BOT_TOKEN", "PASSWORD=")):
   continue
  print(f"{i+1}: {line[:230]}")
