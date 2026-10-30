"""Safely provision the 48 staged Word assets from the approved ZIP archive.

Usage: python scripts/install_rpt_pj_2027_assets.py ARCHIVE.zip /path/to/data
No existing file is overwritten. This does not modify app.py or enable access.
"""
from pathlib import Path
from zipfile import ZipFile
import sys

from rpt_pj_2027_delivery import FILE_PATTERN, STATES, YEARS


def install(archive, destination):
    expected = {
        "RPT_PJ_2027_DOCX/" + FILE_PATTERN.format(state=state, year=year)
        for state in STATES for year in YEARS
    }
    destination = Path(destination)
    with ZipFile(archive) as z:
        names = {info.filename for info in z.infolist() if not info.is_dir()}
        if names != expected:
            raise ValueError(
                f"Unexpected RPT assets: missing={len(expected - names)} "
                f"extra={len(names - expected)}"
            )
        for info in z.infolist():
            if info.is_dir():
                continue
            if info.file_size > 2_000_000:
                raise ValueError("Unexpectedly large RPT file")
        for name in sorted(expected):
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise FileExistsError(f"Refusing overwrite: {target}")
            with z.open(name) as src, target.open("xb") as out:
                import shutil
                shutil.copyfileobj(src, out)
    return len(expected)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: install_rpt_pj_2027_assets.py ARCHIVE.zip DATA_DIR")
    print("Installed", install(sys.argv[1], sys.argv[2]), "Word files")
