"""Print only static fragments of app.py about Telegram teacher profile/timetable.

No Telegram bot/network calls, no DB mutations.
"""
from pathlib import Path
p=Path("app.py");lines=p.read_text("utf-8").splitlines()
ranges=[
 (12408,12696),(14578,14647),(15979,16035),
 (39409,39452),(39687,39733),(39789,39829),
 (40551,40640),(46925,47024)
]
for start,end in ranges:
 print("SECTION",start,end)
 for i in range(start-1,min(end,len(lines))):
  line=lines[i]
  if any(x in line.upper() for x in ("TOKEN=", "SECRET=", "API_KEY=", "BOT_TOKEN", "PASSWORD=")):
    print(f"{i+1}: [CONFIG REDACTED]");continue
  print(f"{i+1}: {line[:200]}")
