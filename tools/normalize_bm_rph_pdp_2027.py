#!/usr/bin/env python3
"""Normalize visible Bahasa Melayu RPH terminology (Lesson -> PdP) safely.
All filenames and IDs are deliberately retained to avoid breaking adapters.
"""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
root=ROOT/"rph_standalone/bahasa_melayu"
total=0
changes=[]
for y in range(2,7):
    path=root/f"year{y}"
    for p in sorted(path.glob("lesson_*.md")):
        before=p.read_text(encoding="utf-8")
        after,count=re.subn(r"\bLesson\b","PdP",before)
        if count:
            p.write_text(after,encoding="utf-8")
            total+=count
            changes.append(p.as_posix())
    assert len(list(path.glob("lesson_*.md")))==({2:164,3:165,4:165,5:166,6:165}[y])
print(f"Normalized {total} occurrences across {len(changes)} files",flush=True)
if __name__=="__main__":
    assert total>0
