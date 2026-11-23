"""CI freeze: block additional paid KSSR BM Word files in a PUBLIC repo.

WARNING: Five grandfathered Word files remain public in git history.
This guard only prevents further additions/changes pending private migration.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = "rpt_2027/kssr_word_premium/"
KNOWN_PUBLIC = {
    "rpt_2027/kssr_word_premium/bahasa_melayu/tahun_2.docx": "29f5c6431af6f9ec006c624485ed2e8d7ee5f7f01c52f243b24f9021a7bd0170",
    "rpt_2027/kssr_word_premium/bahasa_melayu/tahun_3.docx": "c8602d7fe24bfa6f1f60995d92cf4b705ece128f61a9912142a11a10953f3b5f",
    "rpt_2027/kssr_word_premium/bahasa_melayu/tahun_4.docx": "9d2414c0b920d55ed88df7bdbf27c0b1ecfff9f2ee2795910d3336f04796fda4",
    "rpt_2027/kssr_word_premium/bahasa_melayu/tahun_5.docx": "24320f38567d967e1de1b21e6af8d4ac0cb3f87e73a76ac0d2e456e18f12659f",
    "rpt_2027/kssr_word_premium/bahasa_melayu/tahun_6.docx": "0aa080bd40ccfea11fcaf2f3235148c845e23d359928d6190e48c8a3ac431e06",
}

def evaluate(tracked: set[str], file_hashes: dict[str, str]) -> list[str]:
    """Pure validation for CI and unit tests."""
    found = {s for s in tracked if s.startswith(PUBLIC_DIR) and s.lower().endswith(".docx")}
    errors = []
    for path in sorted(found - set(KNOWN_PUBLIC)):
        errors.append("NEW_PUBLIC_WORD_FILE " + path)
    for path in sorted(set(KNOWN_PUBLIC) & found):
        if file_hashes.get(path) != KNOWN_PUBLIC[path]:
            errors.append("EXISTING_PUBLIC_WORD_CHANGED " + path)
    return errors

def main() -> int:
    try:
        raw = subprocess.check_output(["git", "ls-files", "-z", "--", PUBLIC_DIR], cwd=ROOT)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: unable to list tracked files: {exc}", file=sys.stderr)
        return 2
    tracked = {s.decode("utf-8") for s in raw.split(b"\\0") if s}
    hashes = {}
    for path in tracked & set(KNOWN_PUBLIC):
        source = ROOT / path
        if source.is_file() and not source.is_symlink():
            hashes[path] = hashlib.sha256(source.read_bytes()).hexdigest()
    problems = evaluate(tracked, hashes)
    if problems:
        print("\\n".join("BLOCK: " + line for line in problems), file=sys.stderr)
        return 1
    print("FREEZE PASS: no additional or modified paid KSSR BM Word files.")
    print("SECURITY DEBT: five public files remain; see GitHub issue #1306.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
