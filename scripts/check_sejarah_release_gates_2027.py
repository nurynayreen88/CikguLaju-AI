#!/usr/bin/env python3
"""Contract QA: Sejarah 2027 must remain blocked while evidence incomplete."""
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from web.sejarah_2027_staging_source import SejarahNotReady, lesson, preview_only, source_fingerprint

count=0
for y in (4,5,6):
    hashes=set()
    for n in range(1,37):
        row=preview_only(y,n)
        assert row["id"]==f"SEJ-T{y}-PDP-{n:03d}"
        identity=source_fingerprint(y,n)
        assert re.fullmatch(r"[0-9a-f]{64}",identity)
        hashes.add(identity)
        try:
            lesson(y,n)
        except SejarahNotReady:
            pass
        else:
            raise AssertionError(f"Unsafe Sejarah public release for Year {y} PdP {n}")
        count+=1
    assert len(hashes)==36
for args in [(3,1),(7,1),(4,0),(4,37),(4,True),(True,1)]:
    try:
        preview_only(*args)
    except ValueError:
        pass
    else:
        raise AssertionError("Accepted invalid identifier "+str(args))
print(f"Sejarah fail-closed source contract: {count} / 108 previewable; all 108 public exports BLOCKED; 108 immutable fingerprints")
