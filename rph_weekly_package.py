"""Package successfully generated weekly RPH files without modifying source files."""
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import PurePosixPath

def weekly_zip(documents: dict[str, bytes]) -> bytes:
    """Accept trusted document bytes; reject traversal and duplicate archive names."""
    if not documents:
        raise ValueError("No successful RPH documents to package")
    buffer = BytesIO()
    seen = set()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, content in sorted(documents.items()):
            path = PurePosixPath(name)
            if (not name or name.startswith("/") or "\\" in name
                or any(part in ("..", ".") for part in name.split("/"))
                or path.suffix.lower() not in (".pdf", ".docx")
                or not isinstance(content, bytes) or not content):
                raise ValueError("Unsafe or empty RPH document")
            normalized = str(path).casefold()
            if normalized in seen:
                raise ValueError("Duplicate archive document")
            seen.add(normalized)
            archive.writestr(str(path), content)
    return buffer.getvalue()
