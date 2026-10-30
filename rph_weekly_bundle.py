"""Build a ZIP of weekly RPH documents with a human-readable result manifest.

No external file paths are read; callers provide bytes from the existing RPH engine.
"""
import csv
from io import BytesIO, StringIO
from zipfile import ZipFile, ZIP_DEFLATED
from rph_weekly_package import weekly_zip

def weekly_result_bundle(documents: dict[str, bytes], results: list[dict]) -> bytes:
    """Results are status metadata, never trusted as paths."""
    if not documents:
        raise ValueError("No successful documents to bundle")
    required = ("session_id", "status", "detail")
    seen = set()
    for result in results:
        if not all(k in result for k in required):
            raise ValueError("Incomplete result row")
        if result["session_id"] in seen:
            raise ValueError("Duplicate session result")
        if result["status"] not in ("succeeded", "failed", "skipped"):
            raise ValueError("Unsupported status")
        seen.add(result["session_id"])
    csv_text = StringIO()
    writer = csv.DictWriter(csv_text, fieldnames=required, extrasaction="ignore")
    writer.writeheader()
    for row in results:
        # Prefix formula-like content to prevent spreadsheet formula injection.
        safe = {k: str(row[k]) for k in required}
        for k, value in safe.items():
            if value.lstrip().startswith(("=", "+", "-", "@")):
                safe[k] = "'" + value
        writer.writerow(safe)
    source = BytesIO(weekly_zip(documents))
    output = BytesIO()
    with ZipFile(source, "r") as src, ZipFile(output, "w", ZIP_DEFLATED) as dst:
        for item in src.infolist():
            dst.writestr(item.filename, src.read(item.filename))
        dst.writestr("ringkasan_penjanaan.csv", csv_text.getvalue().encode("utf-8-sig"))
    return output.getvalue()
