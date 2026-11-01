"""Check English standalone lesson filenames without changing any files.

The canonical filename is lesson_NNN.md. Legacy names are reported separately
and are not silently treated as approved content.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english"


def inventory(root=ROOT):
    result = {}
    for year in (1, 2, 3):
        folder = Path(root) / f"year{year}"
        actual = {p.name for p in folder.glob("lesson_*.md") if p.is_file()}
        expected = {f"lesson_{n:03d}.md" for n in range(1, 161)}
        result[f"year{year}"] = {
            "canonical_count": len(expected & actual),
            "missing_canonical": sorted(expected - actual),
            "noncanonical": sorted(actual - expected),
        }
    return result


if __name__ == "__main__":
    print(json.dumps(inventory(), ensure_ascii=False, indent=2))
