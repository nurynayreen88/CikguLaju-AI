"""One-time logo + school name for each paid RPT 2027 Telegram PDF download.

This adapter does not write to the user profile, Supabase, SQLite, file
library, or curriculum data. School name and Telegram logo file_id live in
a bounded in-memory state for a single attempt, and are discarded afterwards.
It is installed last, after all existing callback wrappers.
"""
from __future__ import annotations

import html
import io
import re
import threading
import time
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory

import requests

SESSION_SECONDS = 20 * 60
MAX_LOGO_BYTES = 4 * 1024 * 1024
_CALLBACKS = {
    "rpt2027_en_pdf_": ("english", "English"),
    "rpt2027_bm_pdf_": ("bm", "Bahasa Melayu"),
    "rpt2027_math_pdf_": ("math", "Matematik"),
    "rpt2027_pi_pdf_": ("pi", "Pendidikan Islam"),
    "rpt2027_pjpk_pdf_": ("pjpk", "PJPK"),
    "rpt2027_pm_ab_pdf_": ("pm", "Pendidikan Moral"),
    "rpt2027_psv_pdf_": ("psv", "Pendidikan Seni Visual"),
    # Saved buttons from earlier Moral menus also use the current single PDF.
    "rpt2027_pm_96_a_": ("pm", "Pendidikan Moral"),
    "rpt2027_pm_96_b_": ("pm", "Pendidikan Moral"),
    "rpt2027_pm_pdf_": ("pm", "Pendidikan Moral"),
}

_STATIC = {
    "english": "rpt_2027.english.telegram_downloads",
    "bm": "rpt_2027.bahasa_melayu.telegram_downloads",
    "math": "rpt_2027.matematik.telegram_downloads",
    "pi": "rpt_2027.pendidikan_islam.telegram_downloads",
    "pjpk": "rpt_2027.pjpk.telegram_downloads",
}

def selection(data):
    """Return (subject, display label, year) or None for unrelated callbacks."""
    if not isinstance(data, str):
        return None
    for prefix, (subject, label) in _CALLBACKS.items():
        if data.startswith(prefix):
            year = data[len(prefix):]
            return (subject, label, int(year)) if year in ("2","3","4","5","6") else (subject,label,None)
    return None

def school_name(value):
    """Reject commands, markup and unreasonable names; do not persist it."""
    if not isinstance(value, str) or value.lstrip().startswith("/"):
        return ""
    name = " ".join("".join(ch for ch in value if ch.isprintable() and ch not in "<>{}").split())
    if not 3 <= len(name) <= 95:
        return ""
    return name

def image_file_id(message):
    """Recognize PNG/JPEG Telegram images only, never payment PDFs or other files."""
    photos = message.get("photo")
    if isinstance(photos, list) and photos:
        p = photos[-1]
        if isinstance(p, dict) and 0 < int(p.get("file_size") or 1) <= MAX_LOGO_BYTES:
            return p.get("file_id") or None
    doc = message.get("document")
    if isinstance(doc, dict) and doc.get("file_id"):
        mime = str(doc.get("mime_type") or "").lower()
        if mime in ("image/jpeg","image/png") and 0 < int(doc.get("file_size") or 1) <= MAX_LOGO_BYTES:
            return doc["file_id"]
    return None

def download_logo(rt, file_id):
    """Bounded Telegram file fetch. Never log or persist bot token or image."""
    if not isinstance(file_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{10,512}",file_id):
        raise ValueError("Invalid logo file ID")
    lookup = requests.get(str(rt.API)+"/getFile", params={"file_id":file_id}, timeout=15)
    lookup.raise_for_status()
    result = lookup.json()
    path = (result.get("result") or {}).get("file_path") if result.get("ok") else None
    if (not isinstance(path,str) or not re.fullmatch(r"[A-Za-z0-9_./-]{1,300}",path)
            or ".." in path.split("/")):
        raise ValueError("Invalid Telegram logo path")
    with requests.get("https://api.telegram.org/file/bot"+str(rt.BOT_TOKEN)+"/"+path,
                      stream=True,timeout=30) as response:
        response.raise_for_status()
        pieces=[]
        size=0
        for chunk in response.iter_content(chunk_size=65536):
            size += len(chunk)
            if size > MAX_LOGO_BYTES:
                raise ValueError("Logo exceeds 4 MB")
            pieces.append(chunk)
    raw=b"".join(pieces)
    if not raw:
        raise ValueError("Empty logo")
    # Decode and re-encode the image in memory to strip EXIF and other metadata.
    from PIL import Image, ImageOps, UnidentifiedImageError
    try:
        with Image.open(io.BytesIO(raw)) as original:
            if original.format not in ("JPEG","PNG"):
                raise ValueError("Logo must be JPG or PNG")
            if original.width*original.height > 18_000_000 or min(original.size)<4:
                raise ValueError("Logo image dimensions not supported")
            original.load()
            img=ImageOps.exif_transpose(original)
            img.thumbnail((900,900), Image.Resampling.LANCZOS)
            if img.mode in ("RGBA","LA") or "transparency" in img.info:
                rgb=Image.new("RGB",img.size,"white")
                rgb.paste(img.convert("RGBA"),mask=img.convert("RGBA").getchannel("A"))
            else:
                rgb=img.convert("RGB")
            output=io.BytesIO()
            rgb.save(output,format="PNG",optimize=True)
            return output.getvalue()
    except (UnidentifiedImageError,OSError,ValueError) as exc:
        raise ValueError("Logo PNG/JPG tidak sah") from exc

def original_rpt(subject,year,folder):
    """Use the exact source for the selected subject/year, fail closed."""
    if subject in _STATIC:
        module=import_module(_STATIC[subject])
        if subject=="english":
            path=module.pdf_path(year)
            if not path.is_file():
                raise ValueError("English RPT unavailable")
        elif not module.pdf_ready(year):
            raise ValueError("RPT source unavailable")
        else:
            path=module.pdf_path(year)
        if path.stat().st_size<2000:
            raise ValueError("RPT PDF missing")
        return path
    if subject=="pm":
        module=import_module("rpt_2027.pendidikan_moral.complete_96_downloads")
        if not module.combined_pdf_ready(year):
            raise ValueError("Moral A/B source unavailable")
        return module.build_combined_rpt_pdf(year,folder/"moral_source.pdf")
    if subject=="psv":
        module=import_module("rpt_2027.psv.telegram_downloads")
        if not module.pdf_ready(year):
            raise ValueError("PSV source unavailable")
        return module.build_pdf(year,folder/"psv_source.pdf")
    raise ValueError("Unknown subject")

def personalized_pdf(source, target, name, logo_png, subject, label, year):
    """White cover with school logo/name; preserve every existing curriculum page."""
    from PIL import Image
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pypdf import PdfReader, PdfWriter

    source=Path(source)
    target=Path(target)
    if source.resolve()==target.resolve() or not source.is_file():
        raise ValueError("Cannot overwrite source RPT")
    if not school_name(name) or type(year) is not int or year not in range(2,7):
        raise ValueError("Invalid cover inputs")
    font,bold="Helvetica","Helvetica-Bold"
    regular=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    strong=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if regular.is_file() and strong.is_file():
        if "RPTLogoReg" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("RPTLogoReg",str(regular)))
            pdfmetrics.registerFont(TTFont("RPTLogoBold",str(strong)))
        font,bold="RPTLogoReg","RPTLogoBold"
    w,h=landscape(A4)
    buf=io.BytesIO()
    cv=canvas.Canvas(buf,pagesize=(w,h))
    cv.setTitle(f"RPT {label} Tahun {year} - {name}")
    cv.setAuthor("CikguLaju AI")
    cv.setFillColor(colors.white)
    cv.rect(0,0,w,h,fill=1,stroke=0)
    cv.setStrokeColor(colors.black)
    cv.setLineWidth(1)
    cv.rect(40,40,w-80,h-80,fill=0,stroke=1)
    cv.setFillColor(colors.black)
    cv.setFont(bold,11)
    cv.drawCentredString(w/2,h-76,"CIKGULAJU AI  |  RPT 2027")
    with Image.open(io.BytesIO(logo_png)) as logo:
        logo.load()
        lw,lh=logo.size
        scale=min(140/lw,115/lh)
        iw,ih=lw*scale,lh*scale
        cv.drawImage(ImageReader(logo), (w-iw)/2, h-235+(115-ih)/2, iw,ih,mask="auto")
    # Wrap long school names without clipping the surrounding cover.
    words=name.split()
    lines=[]
    line=""
    for word in words:
        candidate=(line+" "+word).strip()
        if line and pdfmetrics.stringWidth(candidate,bold,16)>w-125:
            lines.append(line)
            line=word
        else:
            line=candidate
    if line:
        lines.append(line)
    if len(lines)>3 or any(pdfmetrics.stringWidth(line,bold,16)>w-115 for line in lines):
        raise ValueError("School name too long for cover")
    cv.setFont(bold,16)
    for i,line in enumerate(lines):
        cv.drawCentredString(w/2,h-262-i*23,line)
    bottom_of_name=h-262-(len(lines)-1)*23
    cv.setFont(bold,20)
    cv.drawCentredString(w/2,bottom_of_name-65,"RANCANGAN PENGAJARAN TAHUNAN")
    cv.setFont(bold,15)
    cv.drawCentredString(w/2,bottom_of_name-99,(label+" - TAHUN "+str(year)).upper())
    cv.setFont(bold,15)
    cv.drawCentredString(w/2,bottom_of_name-129,"2027")
    cv.setFont(font,9)
    cv.drawCentredString(w/2,76,"RPT Kumpulan A / B  |  Tarikh PdP tertakluk kepada takwim dan jadual sekolah")
    cv.showPage()
    cv.save()
    buf.seek(0)
    current=PdfReader(str(source))
    if len(current.pages)<1:
        raise ValueError("Source PDF has no pages")
    # Those three RPT types already begin with a dedicated title-only cover.
    # All other subjects may have actual week-one content on page 1.
    skip=1 if subject in ("english","pm","psv") else 0
    if skip and len(current.pages)<2:
        raise ValueError("Expected RPT cover and curriculum pages")
    result=PdfWriter()
    result.add_page(PdfReader(buf).pages[0])
    for page in current.pages[skip:]:
        result.add_page(page)
    with target.open("wb") as stream:
        result.write(stream)
    verify=PdfReader(str(target))
    if len(verify.pages) != len(current.pages)+1-skip:
        raise RuntimeError("Personalized PDF did not preserve source pages")
    return target

def install(runtime):
    """Intercept only selected RPT downloads and one-time subsequent chat input."""
    if getattr(runtime,"CIKGULAJU_RPT2027_LOGO_ONCE_ACTIVE",False):
        return True
    for key in ("callback","send","send_document","_access_info","_is_admin","app","request","jsonify","BOT_TOKEN","API"):
        if not hasattr(runtime,key):
            return False
    original_callback=runtime.callback
    sessions={}
    seen_updates={}
    lock=threading.RLock()

    def allowed(cid):
        try:
            return bool(runtime._is_admin(cid) or runtime._access_info(cid).get("active"))
        except Exception:
            return False

    def remember(cid):
        with lock:
            item=sessions.get(cid)
            if item and (time.monotonic()-item["started"]>SESSION_SECONDS):
                sessions.pop(cid,None)
                return None
            return item

    def callback(cid,data):
        choice=selection(str(data or ""))
        if choice is not None:
            subject,label,year=choice
            if year is None or type(cid) is not int or cid<=0:
                return runtime.send(cid,"Pilihan RPT atau chat tidak sah.")
            if not allowed(cid):
                with lock: sessions.pop(cid,None)
                return runtime.send(cid,"RPT 2027 hanya untuk Rakan Pembangun dan pelanggan aktif.",
                    [[{"text":"Jadi Rakan Pembangun","callback_data":"pioneer_join"}],
                     [{"text":"Menu Utama","callback_data":"home"}]])
            try:
                original_rpt(subject,year,Path("/tmp"))
            except Exception:
                return runtime.send(cid,"PDF RPT pilihan ini belum tersedia. Cuba tahun atau subjek lain.")
            with lock:
                sessions[cid]={"subject":subject,"label":label,"year":year,
                               "phase":"name","started":time.monotonic()}
            return runtime.send(cid,
                f"RPT 2027 - <b>{html.escape(label)} Tahun {year}</b>\n\n"
                "Sila <b>taip nama sekolah</b> untuk muka depan PDF ini.\n\n"
                "Selepas itu bot akan meminta gambar logo sekolah. "
                "Maklumat ini diminta semula setiap kali muat turun dan tidak disimpan dalam profil.",
                [[{"text":"Batalkan","callback_data":"rpt2027_logo_cancel"}]])
        if str(data or "")=="rpt2027_logo_cancel":
            with lock: item=sessions.pop(cid,None)
            year=(item or {}).get("year")
            buttons=[[{"text":"Pilih Subjek Semula","callback_data":f"rpt2027_year_{year}"}]] if year else []
            buttons.append([{"text":"Menu Utama","callback_data":"home"}])
            return runtime.send(cid,"Permintaan RPT dibatalkan. Logo dan nama sekolah tidak disimpan.",buttons)
        with lock:
            sessions.pop(cid,None)
        return original_callback(cid,data)

    def complete(cid,request_data):
        """Run after webhook ACK; never retain bytes beyond this single download."""
        try:
            if not allowed(cid):
                runtime.send(cid,"Akses RPT sudah tidak aktif. Sila semak langganan.")
                return
            raw=download_logo(runtime,request_data["file_id"])
            with TemporaryDirectory(prefix="cikgulaju_rpt_once_") as folder:
                tmp=Path(folder)
                src=original_rpt(request_data["subject"],request_data["year"],tmp)
                output=personalized_pdf(src,tmp/f"RPT_{request_data['subject']}_Tahun_{request_data['year']}_2027.pdf",
                    request_data["name"],raw,request_data["subject"],
                    request_data["label"],request_data["year"])
                result=runtime.send_document(cid,str(output),
                    f"RPT {request_data['label']} Tahun {request_data['year']} 2027 - {request_data['name']}")
                check=getattr(runtime,"_telegram_delivery_ok_v25279",None)
                ok=bool(check(result)) if callable(check) else bool(
                    getattr(result,"ok",False) and (result.json() or {}).get("ok") is True)
                if not ok:
                    runtime.send(cid,"Telegram belum mengesahkan penghantaran RPT. Sila pilih subjek semula.")
        except ValueError as exc:
            # This message is intended for the user; never include a Telegram token.
            runtime.send(cid,"Logo atau RPT tidak dapat diproses. Gunakan logo JPG/PNG bawah 4 MB dan cuba semula.")
        except Exception as exc:
            print("RPT personalisasi sementara gagal:",type(exc).__name__,flush=True)
            runtime.send(cid,"RPT belum berjaya dihantar. Sila pilih subjek semula.")
        finally:
            with lock:
                current=sessions.get(cid)
                if current and current.get("phase")=="generating" and current.get("started")==request_data["started"]:
                    sessions.pop(cid,None)

    def before_webhook():
        req=runtime.request
        if req.path!="/webhook" or req.method!="POST":
            return None
        update=req.get_json(silent=True) or {}
        message=update.get("message")
        if not isinstance(message,dict):
            return None
        chat=message.get("chat") or {}
        sender=message.get("from") or {}
        cid=chat.get("id")
        if (not isinstance(cid,int) or cid<=0 or chat.get("type")!="private"
                or sender.get("id")!=cid):
            return None
        item=remember(cid)
        if not item:
            return None
        text=(message.get("text") or "").strip()
        if text.startswith("/") or text in ("☰ Menu","Menu"):
            with lock: sessions.pop(cid,None)
            return None   # The existing Telegram command handler runs normally.
        update_id=update.get("update_id")
        with lock:
            now=time.monotonic()
            if len(seen_updates)>3000:
                for key,at in list(seen_updates.items()):
                    if now-at>3600:
                        seen_updates.pop(key,None)
            if isinstance(update_id,int) and update_id in seen_updates:
                return runtime.jsonify({"ok":True,"duplicate":True})
            if isinstance(update_id,int):
                seen_updates[update_id]=now
            phase=item["phase"]
            if phase=="name":
                name=school_name(text)
                if name:
                    item["name"]=name
                    item["phase"]="logo"
            elif phase=="logo":
                file_id=image_file_id(message)
                if file_id:
                    item["phase"]="generating"
                    transfer={"file_id":file_id,"subject":item["subject"],"label":item["label"],
                        "year":item["year"],"name":item["name"],"started":item["started"]}
            else:
                transfer=None
        if phase=="name":
            if not name:
                runtime.send(cid,"Taip nama sekolah yang sah (3 hingga 95 aksara) dahulu.")
            else:
                runtime.send(cid,f"Nama sekolah: <b>{html.escape(name)}</b>\n\n"
                    "Sekarang <b>hantar gambar logo sekolah</b> sebagai foto atau fail JPG/PNG (maksimum 4 MB).",
                    [[{"text":"Batalkan","callback_data":"rpt2027_logo_cancel"}]])
        elif phase=="logo":
            if not file_id:
                runtime.send(cid,"Sila hantar gambar logo dalam format JPG/PNG, maksimum 4 MB. "
                    "Jangan hantar PDF atau resit bayaran.")
            else:
                runtime.send(cid,"Logo diterima. PDF RPT sedang dijana untuk muat turun ini sahaja.")
                threading.Thread(target=complete,args=(cid,transfer),daemon=True).start()
        else:
            runtime.send(cid,"PDF sedang diproses. Untuk permintaan baharu, pilih semula RPT selepas selesai.")
        return runtime.jsonify({"ok":True,"rpt_personalized":True})

    runtime.callback=callback
    runtime.app.before_request(before_webhook)
    runtime.CIKGULAJU_RPT2027_LOGO_ONCE_ACTIVE=True
    return True
