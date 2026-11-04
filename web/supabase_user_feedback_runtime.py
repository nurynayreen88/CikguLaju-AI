"""Persist CikguLaju teacher feedback in Supabase, including admin review/PDF.

Server-side admin identity is checked on every detail/status/list callback.
The existing local SQLite feedback remains untouched for recovery/audit.
"""
import html
import os
import tempfile


def enabled():
    return os.getenv("CIKGULAJU_SUPABASE_USER_RECORDS", "0").lower() in (
        "1","true","yes"
    )


def _one(result):
    if isinstance(result, list):
        return result[0] if result else None
    return result if isinstance(result, dict) else None


def install(runtime):
    if not enabled():
        return False
    sb = runtime._sb_request
    send = runtime.send
    original_callback = runtime.callback
    original_counts = runtime._admin_counts

    def feedback_counts():
        result = _one(sb("POST","rpc/bot_feedback_status_counts",json={}))
        if not isinstance(result,dict):
            raise RuntimeError("Feedback counts unavailable")
        return {key:int(result[key]) for key in ("total","baru","dibaca","selesai")}

    def admin_counts():
        result = dict(original_counts())
        counts = feedback_counts()
        result["feedback"] = counts["total"]
        result["new_feedback"] = counts["baru"]
        result["read_feedback"] = counts["dibaca"]
        result["done_feedback"] = counts["selesai"]
        return result

    def users():
        rows = runtime._admin_persistent_users()
        return {str(r.get("chat_id")):r for r in rows}

    def save_feedback(cid,text,category="Umum"):
        uid = int(cid)
        if uid <= 0:
            return False
        cleaned = " ".join(str(text or "").split())[:2000]
        if not cleaned:
            return False
        payload = {"chat_id": str(uid), "category": str(category or "Umum")[:100],
                   "feedback_text": cleaned}
        try:
            result = sb("POST","bot_user_feedback",json=payload,
                        prefer="return=representation")
            row = _one(result)
            if not row or not row.get("id"):
                raise RuntimeError("Supabase did not acknowledge feedback")
        except Exception as exc:
            print("DURABLE USER feedback save failed:",type(exc).__name__,flush=True)
            return False
        admin_cid = runtime.ADMIN_CHAT_ID
        if admin_cid:
            try:
                send(admin_cid,
                     f"🔔 <b>KOMEN / CADANGAN BARU #{int(row['id'])}</b>\n"
                     f"Pengguna: <code>{uid}</code>\n"
                     f"Kategori: <b>{html.escape(str(category or 'Umum'))}</b>\n\n"
                     + html.escape(cleaned),
                     [[{"text":"📖 BACA KOMEN","callback_data":
                        f"admin_feedback_view|{int(row['id'])}"}],
                      [{"text":"💬 SEMUA KOMEN","callback_data":"admin_feedback|0"}]])
            except Exception as exc:
                print("DURABLE USER feedback admin notification:",
                      type(exc).__name__,flush=True)
        return True

    def feedback_row(fid):
        rows = sb("GET",f"bot_user_feedback?id=eq.{int(fid)}&select=*&limit=1")
        return _one(rows)

    def feedback_card(cid,fid):
        if not runtime._is_admin(cid):
            return send(cid,"⛔ Paparan ini hanya untuk admin.")
        if fid <= 0:
            return send(cid,"⚠️ ID komen tidak sah.")
        row = feedback_row(fid)
        if not row:
            return send(cid,"ℹ️ Komen tidak ditemui.",
                        [[{"text":"💬 Semua Komen","callback_data":"admin_feedback|0"}]])
        person = users().get(str(row["chat_id"])) or {}
        name = html.escape(runtime._admin_user_name(person))
        status = str(row["status"])
        icon = {"baru":"🆕 BARU","dibaca":"👀 DIBACA","selesai":"✅ SELESAI"}.get(
            status,status.upper())
        txt = (f"💬 <b>KOMEN & CADANGAN #{fid}</b>\n\n"
               f"👤 <b>{name}</b>\nID Telegram: <code>{row['chat_id']}</code>\n"
               f"📅 {html.escape(str(row['created_at'])[:19])}\n"
               f"🏷️ {html.escape(row['category'])}\nStatus: <b>{icon}</b>\n\n"
               f"{html.escape(row['feedback_text'])}")
        kb = []
        for value,caption in (("dibaca","👀 TANDA DIBACA"),
                              ("selesai","✅ TANDA SELESAI"),
                              ("baru","🆕 KEMBALIKAN KE BARU")):
            if value != status:
                kb.append([{"text":caption,
                            "callback_data":f"admin_feedback_status|{fid}|{value}"}])
        kb.append([{"text":"👤 Lihat Pengguna","callback_data":
                    f"admin_user|{row['chat_id']}"},
                   {"text":"💬 Semua Komen","callback_data":"admin_feedback|0"}])
        return send(cid,txt,kb)

    def set_feedback_status(fid,status):
        if status not in ("baru","dibaca","selesai") or int(fid) <= 0:
            return False
        result = sb("PATCH",f"bot_user_feedback?id=eq.{int(fid)}",
                    json={"status":status},prefer="return=representation")
        return _one(result) is not None

    def list_feedback(cid,page):
        if not runtime._is_admin(cid):
            return send(cid,"⛔ Panel ini hanya untuk admin.")
        page = max(0,min(int(page),10000))
        per=6
        records = sb("GET","bot_user_feedback?select=*"
                     f"&order=status.asc,id.desc&limit={per+1}&offset={per*page}")
        if not isinstance(records,list):
            raise RuntimeError("Feedback list unavailable")
        counts = feedback_counts()
        people = users()
        text = (f"💬 <b>KOMEN & CADANGAN — SUPABASE</b>\n\n"
                f"🆕 Baru: <b>{counts['baru']}</b>   "
                f"👀 Dibaca: <b>{counts['dibaca']}</b>   "
                f"✅ Selesai: <b>{counts['selesai']}</b>\n"
                f"Jumlah: <b>{counts['total']}</b>")
        kb=[]
        if not records: text+="\n\nBelum ada feedback."
        for row in records[:per]:
            person=people.get(str(row["chat_id"])) or {}
            name=runtime._admin_user_name(person)[:18]
            icon={"baru":"🆕","dibaca":"👀","selesai":"✅"}.get(row["status"],"•")
            preview=" ".join(row["feedback_text"].split())[:46]
            kb.append([{"text":f"{icon} #{row['id']} {name} — {preview}",
                        "callback_data":f"admin_feedback_view|{row['id']}"}])
        kb.append([{"text":"📄 PDF Semua","callback_data":"admin_feedback_pdf|all"},
                   {"text":"📄 Belum Selesai","callback_data":"admin_feedback_pdf|open"}])
        kb.append([{"text":"📄 PDF Selesai","callback_data":"admin_feedback_pdf|done"}])
        nav=[]
        if page:
            nav.append({"text":"⬅️","callback_data":f"admin_feedback|{page-1}"})
        nav.append({"text":"🛠️ PANEL","callback_data":"admin_panel"})
        if len(records)>per:
            nav.append({"text":"➡️","callback_data":f"admin_feedback|{page+1}"})
        kb.append(nav)
        return send(cid,text,kb)

    def report_rows(scope):
        if scope not in ("all","open","done"):
            raise ValueError("Invalid PDF report scope")
        result=[]
        offset=0
        while True:
            q="bot_user_feedback?select=*&order=id.desc&limit=200"
            q+=f"&offset={offset}"
            if scope=="done":q+="&status=eq.selesai"
            elif scope=="open":q+="&status=neq.selesai"
            batch=sb("GET",q)
            if not isinstance(batch,list):
                raise RuntimeError("Feedback PDF data unavailable")
            result.extend(batch)
            offset+=len(batch)
            if len(batch)<200:
                return result
            if offset>10000:
                raise RuntimeError("Too many feedback rows for one PDF")

    def feedback_pdf(cid,scope="all"):
        if not runtime._is_admin(cid):
            return send(cid,"⛔ Paparan ini hanya untuk admin.")
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        )
        rows=report_rows(scope)
        people=users()
        labels={"all":"Semua Komen & Cadangan","open":"Belum Selesai",
                "done":"Selesai"}
        with tempfile.TemporaryDirectory(prefix="cikgulaju_feedback_") as folder:
            path=os.path.join(folder,f"CikguLaju_Feedback_{scope}.pdf")
            styles=getSampleStyleSheet()
            title=ParagraphStyle("FbTitle",parent=styles["Title"],
                fontName="Helvetica-Bold",fontSize=15,alignment=TA_CENTER)
            body=styles["BodyText"]
            doc=SimpleDocTemplate(path,pagesize=A4,rightMargin=14*mm,
                                  leftMargin=14*mm,topMargin=14*mm,bottomMargin=14*mm)
            story=[Paragraph("LAPORAN KOMEN DAN CADANGAN CIKGULAJU",title),
                   Paragraph(f"<b>{html.escape(labels[scope])}</b>: "
                             f"{len(rows)} rekod",body),
                   Spacer(1,6*mm)]
            for row in rows:
                person=people.get(str(row["chat_id"])) or {}
                name=runtime._admin_user_name(person)
                text=(
                    f"<b>#{row['id']} {html.escape(name)} "
                    f"— {html.escape(row['status'])}</b>\n"
                    f"<br/>ID {html.escape(str(row['chat_id']))} • "
                    f"{html.escape(str(row['created_at'])[:19])} • "
                    f"{html.escape(row['category'])}\n<br/>"
                    f"{html.escape(row['feedback_text'])}"
                )
                table=Table([[Paragraph(text,body)]],colWidths=[180*mm])
                table.setStyle(TableStyle([
                    ("BOX",(0,0),(-1,-1),0.4,colors.grey),
                    ("BACKGROUND",(0,0),(-1,-1),colors.whitesmoke),
                    ("LEFTPADDING",(0,0),(-1,-1),7),
                    ("RIGHTPADDING",(0,0),(-1,-1),7),
                    ("TOPPADDING",(0,0),(-1,-1),5),
                    ("BOTTOMPADDING",(0,0),(-1,-1),5)
                ]))
                story.extend([table,Spacer(1,3*mm)])
            if not rows:
                story.append(Paragraph("Tiada rekod untuk skop ini.",body))
            doc.build(story)
            runtime.send_document(cid,path,
                                  f"📄 Laporan Maklum Balas — {labels[scope]}")
        return send(cid,"✅ Laporan daripada Supabase berjaya dihantar.",
                    [[{"text":"💬 Kembali ke Komen","callback_data":"admin_feedback|0"}]])

    def callback(cid,d):
        raw=str(d or "")
        if not (raw.startswith("admin_feedback|") or
                raw.startswith("admin_feedback_view|") or
                raw.startswith("admin_feedback_status|") or
                raw.startswith("admin_feedback_pdf|")):
            return original_callback(cid,d)
        if not runtime._is_admin(cid):
            return send(cid,"⛔ Paparan ini hanya untuk admin.")
        try:
            if raw.startswith("admin_feedback|"):
                return list_feedback(cid,int(raw.split("|",1)[1]))
            if raw.startswith("admin_feedback_view|"):
                return feedback_card(cid,int(raw.split("|",1)[1]))
            if raw.startswith("admin_feedback_status|"):
                _,fid,status=raw.split("|",2)
                if not set_feedback_status(int(fid),status):
                    return send(cid,"⚠️ Status komen tidak dapat dikemas kini.")
                return feedback_card(cid,int(fid))
            if raw.startswith("admin_feedback_pdf|"):
                return feedback_pdf(cid,raw.split("|",1)[1])
        except Exception as exc:
            print("DURABLE USER feedback admin action failed:",
                  type(exc).__name__,flush=True)
            return send(cid,"⚠️ Komen di Supabase belum dapat diakses. "
                        "Rekod tidak dipadam atau ditandakan selesai.")
        return send(cid,"⚠️ Butang tidak sah.")

    runtime._save_beta_feedback=save_feedback
    runtime._feedback_counts=feedback_counts
    runtime._feedback_card=feedback_card
    runtime._set_feedback_status=set_feedback_status
    runtime._feedback_pdf=feedback_pdf
    runtime._admin_counts=admin_counts
    runtime.callback=callback
    print("DURABLE USER RECORDS: SUPABASE FEEDBACK ENABLED",flush=True)
    return True
