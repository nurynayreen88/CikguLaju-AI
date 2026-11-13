"""Load checked PdP excerpts into the private Web material bucket."""
import argparse
from hashlib import sha256
import json
import os
import re
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener
from zipfile import ZipFile

from web.native_telegram_rph_client import BlockRedirects
from web.native_telegram_extra_materials_20261106 import MAX_PDF

OBJECT = re.compile(r"buku-teks/sains/tahun-[1-6]/ms-[0-9]{1,2}-[0-9]{1,2}\.pdf")


def checked_excerpts(archives):
    excerpts = {}
    for archive in archives:
        with ZipFile(archive) as bundle:
            rows = json.loads(bundle.read("manifest.json"))
            if bundle.namelist().count("manifest.json") != 1 or len(rows) + 1 != len(bundle.namelist()):
                raise ValueError("Manifest tidak sepadan dengan senarai fail")
            for row in rows:
                path = row["path"]
                if not OBJECT.fullmatch(path) or path in excerpts:
                    raise ValueError("Laluan PDF tidak sah atau berulang")
                info = bundle.getinfo(path)
                if not 450 <= info.file_size <= MAX_PDF or info.file_size != row["bytes"]:
                    raise ValueError(f"Saiz tidak sepadan untuk {path}")
                data = bundle.read(info)
                if not data.startswith(b"%PDF-") or sha256(data).hexdigest() != row["sha256"]:
                    raise ValueError(f"Kandungan tidak sepadan untuk {path}")
                excerpts[path] = data
    return excerpts


def save_excerpts(excerpts, base, key, bucket):
    origin = urlsplit(base)
    if (origin.scheme != "https" or not re.fullmatch(r"[a-z0-9]+\.supabase\.co", origin.netloc)
            or origin.path or origin.query or origin.fragment or not key
            or not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", bucket)):
        raise ValueError("Konfigurasi storan persendirian tidak sah")
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    transport = build_opener(BlockRedirects())
    for path, data in excerpts.items():
        request = Request(f"{base}/storage/v1/object/{bucket}/{path}", data=data, method="POST",
                          headers={**headers, "Content-Type": "application/pdf", "x-upsert": "false"})
        try:
            with transport.open(request, timeout=60) as response:
                if response.status not in (200, 201):
                    raise ValueError(f"Storan menolak {path}")
        except HTTPError as error:
            # Retrying a completed upload is safe if the existing bytes match.
            detail = error.read(2048)
            if error.code != 409 and not (error.code == 400 and b"Duplicate" in detail):
                raise ValueError(f"Storan menolak {path} (HTTP {error.code})") from None
        read = Request(f"{base}/storage/v1/object/authenticated/{bucket}/{path}", headers=headers)
        with transport.open(read, timeout=60) as response:
            if response.read(MAX_PDF + 1) != data:
                raise ValueError(f"Fail tersimpan berbeza untuk {path}")
        print(path, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+")
    parser.add_argument("--apply", action="store_true", help="Upload verified PDFs")
    args = parser.parse_args()
    excerpts = checked_excerpts(args.archives)
    if args.apply:
        save_excerpts(excerpts, os.environ.get("SUPABASE_URL", "").rstrip("/"),
                      os.environ.get("SUPABASE_SECRET_KEY", ""),
                      os.environ.get("CIKGULAJU_MATERIAL_BUCKET", "cikgulaju-materials"))
    print(f"{len(excerpts)} fail PDF disahkan")


if __name__ == "__main__":
    main()
