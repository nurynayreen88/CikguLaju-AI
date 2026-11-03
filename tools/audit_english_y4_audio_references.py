"""Read-only inventory of Year 4 RPH audio references, not audible verification."""
from collections import Counter
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone/english/year4"
TRACK = re.compile(r"(?i)\\b(?:class\\s*)?CD\\s*([123])\\s*(?:track|[-–])\\s*(\\d{1,3})\\b")
results = []
for n in range(1, 161):
    path = ROOT / f"lesson_{n:03d}.md"
    if not path.exists():
        results.append({"lesson": n, "status": "missing_rph", "tracks": []})
        continue
    text = path.read_text(encoding="utf-8")
    tracks = sorted({f"CD{cd}-{int(track)}" for cd, track in TRACK.findall(text)})
    results.append({"lesson": n, "status": "referenced" if tracks else "no_explicit_cd_track", "tracks": tracks})
summary = {"total_lessons": len(results), "with_track_reference": sum(bool(x["tracks"]) for x in results),
           "without_track_reference": sum(not x["tracks"] for x in results),
           "unique_tracks": len(set(t for x in results for t in x["tracks"])),
           "status_counts": dict(Counter(x["status"] for x in results)),
           "lessons": results,
           "verification_limit": "Reference inventory only; no MP3 content or SOW/book alignment was verified."}
print(json.dumps(summary, indent=2))
