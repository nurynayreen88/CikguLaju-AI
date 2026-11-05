"""Read-only duplicate-name audit for English Year 1 standalone RPH.

Detects canonical and legacy filenames referring to the same lesson.
Does not delete, rename, or choose which content is authoritative.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english" / "year1"


def audit(root=ROOT):
    folder = Path(root)
    duplicates = []
    for number in range(1, 161):
        canonical = folder / f"lesson_{number:03d}.md"
        legacy = folder / f"lesson_{number}.md"
        if canonical == legacy or not canonical.is_file() or not legacy.is_file():
            continue
        a, b = canonical.read_bytes(), legacy.read_bytes()
        duplicates.append({
            "lesson": number,
            "canonical": canonical.name,
            "legacy": legacy.name,
            "identical": a == b,
            "canonical_sha256": hashlib.sha256(a).hexdigest(),
            "legacy_sha256": hashlib.sha256(b).hexdigest(),
        })
    return duplicates


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
