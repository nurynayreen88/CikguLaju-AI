"""Immutable RPH source identity shared by Web and Telegram (read-only).

Both deployments must have byte-identical lesson + authoritative mapping files.
Never infer release/approval merely from a matching fingerprint.
"""
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOW_INDEX = "audits/english_primary_2_6_official_sow_index_20261103.json"
PJPK_MANIFEST = "rpt_2027/pjpk/pjpk_2027_rpt_manifest.json"
MAX_SOURCE_BYTES = 2_500_000


def source_paths(year, subject, lesson, component=None):
    if type(year) is not int or type(lesson) is not int:
        return None
    if year == 1 and subject == "ENGLISH" and component is None:
        from web.english_y1_kssr_rph import PLANS
        if lesson in PLANS:
            return (
                "web/english_y1_kssr_rph.py",
                f"rph_standalone/english/year1/lesson_{lesson:03d}.md",
            )
    if not 2 <= year <= 6:
        return None
    if subject == "ENGLISH" and component is None and 1 <= lesson <= 160:
        paths = [
            "rph_standalone/english/year%d/lesson_%03d.md" % (year, lesson),
            SOW_INDEX,
        ]
        if year == 3:
            paths.append("rph_standalone/english/year3/source_task_objectives_20261104.json")
        elif year == 5:
            paths.append("rph_standalone/english/year5/release_approvals_2027.json")
        elif year == 6:
            paths.append("rph_standalone/english/year6/sow_task_overlay_2027.json")
        return tuple(paths)
    if subject == "MORAL" and component is None and 1 <= lesson <= 42:
        return (
            "rph_standalone/pendidikan_moral/year%d/lesson_%03d.md" % (year, lesson),
            "rpt_2027/pendidikan_moral/year%d_crosswalk_DSKP.json" % year,
        )
    if subject == "PJPK" and component in ("PJ", "PK") and 1 <= lesson <= 38:
        return (
            "rph_standalone/pjpk/year%d_%s/lesson_%03d.md" % (year, component.lower(), lesson),
            PJPK_MANIFEST,
        )
    if subject == "PSV" and component is None and 1 <= lesson <= 42:
        return (
            "rph_standalone/psv/year%d/lesson_%03d.md" % (year, lesson),
            "rpt_2027/psv/RPT_PSV_Tahun_%d_2027_DRAF.csv" % year,
        )
    return None


def source_fingerprint(year, subject, lesson, component=None, *, root=ROOT):
    """A digest of exact source bytes, not a generic topic/RPT identifier."""
    paths = source_paths(year, subject, lesson, component)
    if not paths:
        return None
    base = Path(root).resolve()
    digest = sha256()
    for relative in paths:
        candidate = base / relative
        if candidate.is_symlink() or not candidate.is_file():
            return None
        try:
            if not candidate.resolve().is_relative_to(base):
                return None
            if candidate.stat().st_size > MAX_SOURCE_BYTES or candidate.stat().st_size == 0:
                return None
            contents = candidate.read_bytes()
        except (OSError, ValueError):
            return None
        digest.update(relative.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(contents)
        digest.update(b"\x00")
    return digest.hexdigest()
