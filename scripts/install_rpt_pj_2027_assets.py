"""Validate and safely provision the approved 48 RPT PJ 2027 Word files.

Usage: python scripts/install_rpt_pj_2027_assets.py ARCHIVE.zip DATA_DIR
The installer never overwrites existing files. It preflights every target
before copying and rolls back only files it created on failure.
"""
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rpt_pj_2027_delivery import FILE_PATTERN, STATES, YEARS


def install(archive, destination):
    expected = {
        "RPT_PJ_2027_DOCX/" + FILE_PATTERN.format(state=state, year=year)
        for state in STATES for year in YEARS
    }
    destination = Path(destination)
    created = []
    with ZipFile(archive) as z:
        members = [info for info in z.infolist() if not info.is_dir()]
        names = [info.filename for info in members]
        if len(names) not in (48, 49) or set(names) - {"README.txt"} != expected or len(set(names)) != len(names):
            raise ValueError("Archive must contain exactly 48 approved RPT files")
        for info in members:
            if info.filename == "README.txt":
                continue
            if info.file_size == 0 or info.file_size > 2_000_000:
                raise ValueError("Unexpected RPT file size")
            if not info.filename.endswith(".docx"):
                raise ValueError("Unexpected asset type")
        if z.testzip() is not None:
            raise BadZipFile("Corrupted RPT ZIP archive")
        targets = [(name, destination / name) for name in sorted(expected)]
        for _, target in targets:
            if target.exists() or target.is_symlink():
                raise FileExistsError(f"Refusing overwrite: {target}")
        try:
            for name, target in targets:
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(name) as src, target.open("xb") as out:
                    created.append(target)
                    shutil.copyfileobj(src, out)
        except Exception:
            for target in reversed(created):
                target.unlink(missing_ok=True)
            raise
    return len(created)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: install_rpt_pj_2027_assets.py ARCHIVE.zip DATA_DIR")
    print("Installed", install(sys.argv[1], sys.argv[2]), "Word files")
