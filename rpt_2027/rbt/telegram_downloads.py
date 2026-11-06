"""RBT RPT 2027 Telegram paid-only DRAF PDF delivery.

Additional narrow callback; no DB/credit/payment record writes and no other
subject callbacks overwritten. Disabled by default with RBT release flag.
"""
from __future__ import annotations
import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from rpt_2027.rbt.pdf_runtime import pdf_ready,build_pdf

PREFIX="rbt27rpt|"
FLAG="CIKGULAJU_RBT_2027_DRAFT_USER_ENABLED"


def install(ns,*,enabled=None):
    if enabled is None:
        enabled=os.environ.get(FLAG)=="1"
    if not enabled:
        return False
    if ns.get("RBT_2027_RPT_DRAFT_INSTALLED"):
        return True
    required=("callback","send","send_document","_is_admin","_access_info")
    if any(not callable(ns.get(x)) for x in required):
        return False
    if not all(pdf_ready(y) for y in (4,5,6)):
        return False
    previous=ns["callback"]
    send=ns["send"]

    def callback(cid,data):
        value=str(data or "")
        if not value.startswith(PREFIX):
            return previous(cid,data)
        if not re.fullmatch(r"rbt27rpt\|[456]",value):
            return send(cid,"Pilihan RPT RBT tidak sah.")
        year=int(value[-1])
        try:
            allowed=bool(ns["_is_admin"](cid) or ns["_access_info"](cid).get("active"))
        except Exception:
            allowed=False
        if not allowed:
            return send(cid,"RPT RBT 2027 hanya untuk Rakan Pembangun dan pelanggan aktif.",
                        [[{"text":"Jadi Rakan Pembangun","callback_data":"pioneer_join"}],
                         [{"text":"Menu Utama","callback_data":"home"}]])
        if not pdf_ready(year):
            return send(cid,"RPT RBT untuk Tahun ini belum tersedia.")
        try:
            with TemporaryDirectory(prefix="cikgulaju_rbt_rpt_") as temp:
                filename=f"CIKGULAJU_RPT_RBT_TAHUN_{year}_2027_DRAF.pdf"
                file=build_pdf(year,Path(temp)/filename)
                response=ns["send_document"](
                    cid,str(file),f"RPT RBT Tahun {year} 2027 (DRAF SEMAKAN)")
                checker=ns.get("_telegram_delivery_ok_v25279")
                if callable(checker):
                    ok=bool(checker(response))
                else:
                    ok=bool(getattr(response,"ok",False) and response.json().get("ok") is True)
                if not ok:
                    return send(cid,"Telegram belum mengesahkan penghantaran RPT RBT.")
                return response
        except Exception as exc:
            print("RBT RPT delivery failed:",type(exc).__name__,flush=True)
            return send(cid,"RPT RBT PDF tidak berjaya disediakan. Fail lain tidak digunakan.")

    ns["callback"]=callback
    ns["RBT_2027_RPT_DRAFT_INSTALLED"]=True
    return True
