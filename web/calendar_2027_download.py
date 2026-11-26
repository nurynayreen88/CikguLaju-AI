"""Owner-approved original A2 calendar bundled with Web: no upload or storage dependency."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from flask import jsonify,send_file

SHA="546b580c564ef15a7d8b30bb6f27d58be964f001fcb37b24af604248b21088df"
SIZE=158569
NAME="CikguLaju_Kalendar_2027_A2_Kemas.pdf"
PATH=Path(__file__).resolve().parents[1]/"rpt_2027"/"calendar"/NAME

def valid(blob):
    return len(blob)==SIZE and blob.startswith(b"%PDF-") and sha256(blob).hexdigest()==SHA

def read():
    try:
        if PATH.is_symlink() or PATH.stat().st_size!=SIZE:
            return None
        with PATH.open("rb") as f:
            blob=f.read(SIZE+1)
        return blob if valid(blob) else None
    except (OSError,ValueError):
        return None

def install_routes(bp,account_lookup):
    @bp.get("/api/rpt/2027/calendar/status")
    def calendar_status():
        account,error=account_lookup()
        if error is not None:return error
        return jsonify({"ready":read() is not None})

    @bp.get("/api/rpt/2027/calendar.pdf")
    def calendar_download():
        account,error=account_lookup()
        if error is not None:return error
        blob=read()
        if blob is None:return jsonify({"error":"Kalendar belum tersedia."}),503
        response=send_file(BytesIO(blob),mimetype="application/pdf",as_attachment=True,download_name=NAME,conditional=False)
        response.headers["X-Calendar-SHA256"]=SHA
        response.headers["Cache-Control"]="private, no-store"
        return response
