"""Telegram menu for the same read-only 59-item Special Activity RPH catalogue as Web.

The catalogue is DRAFT_REVIEW, not an approved SK/SP syllabus. Every activity,
label, digest and document comes from rph_standalone.aktiviti_khas.engine.
Do not use the ordinary RPH curriculum selector or bypass the existing
Telegram paid/free-trial entitlement RPCs.
"""
from __future__ import annotations

import html
import os
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from rph_standalone.aktiviti_khas import engine

PREFIX = "ak26:"
WEB_URL = "https://cikgulaju-web.onrender.com/"
TRANSISI = engine.TRANSISI
SELEPAS = engine.SELEPAS
PHASES = ("Fasa Penyesuaian", "Fasa Kesediaan")
SUBJECTS = engine.SPECIAL_SUBJECTS


def _button(label, action):
    return {"text": label, "callback_data": PREFIX + action}


def _home_button():
    return [_button("⬅️ Aktiviti Khas", "home"),
            {"text": "🏠 Menu Utama", "callback_data": "home"}]


def _send(runtime, cid, text, rows):
    return runtime.send(cid, text, rows)


def _session(runtime, cid):
    return runtime.state.setdefault(cid, {}).setdefault("_aktiviti_khas_20261110", {})


def _new_session(runtime, cid, kind, year):
    ss = {"kind": kind, "year": year, "delivered": False}
    runtime.state.setdefault(cid, {})["_aktiviti_khas_20261110"] = ss
    return ss


def _esc(value):
    return html.escape(str(value or ""), quote=True)


def _error(runtime, cid, message="Pilihan atau sumber aktiviti telah berubah. Sila pilih semula."):
    return _send(runtime, cid, "⚠️ " + _esc(message),
                 [[_button("🌱 Pilih Aktiviti Khas", "home")],
                  [{"text": "🏠 Menu Utama", "callback_data": "home"}]])


def _kind_page(runtime, cid):
    return _send(
        runtime, cid,
        "🌱 <b>RPH Aktiviti Khas</b>\n\n"
        "Pilih aktiviti tambahan, berasingan daripada Lesson/PdP dan SK/SP rasmi. "
        "<b>59 bahan masih DRAF untuk semakan guru.</b>\n\n"
        "Transisi hanya untuk Tahun 1. Aktiviti selepas tamat sukatan "
        "disediakan khusus mengikut Tahun dan Subjek.",
        [[_button("🌱 Minggu Transisi Tahun 1", "t")],
         [_button("🎨 Selepas Tamat Sukatan", "p")],
         [{"text": "🏠 Menu Utama", "callback_data": "home"}]],
    )


def _transition_page(runtime, cid):
    _new_session(runtime, cid, TRANSISI, 1)
    return _send(runtime, cid, "🌱 <b>Transisi Tahun 1 • DRAF</b>\n\nPilih fasa:",
                 [[_button(name, "tf:" + str(i))] for i, name in enumerate(PHASES)]
                 + [[_button("⬅️ Jenis Aktiviti", "home")]])


def _year_page(runtime, cid):
    return _send(runtime, cid, "🎨 <b>Selepas Tamat Sukatan • DRAF</b>\n\nPilih Tahun:",
                 [[_button("Tahun " + str(y), "py:" + str(y))] for y in range(1, 7)]
                 + [[_button("⬅️ Jenis Aktiviti", "home")]])


def _subject_page(runtime, cid, year):
    _new_session(runtime, cid, SELEPAS, year)
    subjects, digest = engine.list_subjects(SELEPAS, year)
    if len(subjects) != len(SUBJECTS) or [x["value"] for x in subjects] != list(SUBJECTS):
        raise engine.SourceUnavailable("Subject catalogue mismatch")
    return _send(runtime, cid, "📚 <b>Tahun " + str(year) +
                 " • Aktiviti Selepas Tamat Sukatan</b>\n\nPilih subjek (DRAF):",
                 [[_button(row["label"], "ps:" + str(i))]
                  for i, row in enumerate(subjects)]
                 + [[_button("⬅️ Pilih Tahun", "p")]])


def _options_page(runtime, cid, *, phase=None, subject=None):
    ss = _session(runtime, cid)
    kind, year = ss.get("kind"), ss.get("year")
    if kind == TRANSISI:
        if year != 1 or phase not in PHASES or subject is not None:
            raise ValueError("Invalid transition selection")
        ss["phase"] = phase
    else:
        if kind != SELEPAS or year not in range(1, 7) or subject not in SUBJECTS:
            raise ValueError("Invalid post-syllabus selection")
        ss["subject"] = subject
    rows, digest = engine.list_options(kind, year, phase=phase, subject=subject)
    if not rows:
        raise engine.SourceUnavailable("No matching activities")
    ss["digest"] = digest
    ss["options"] = [r["id"] for r in rows]
    ss.pop("activity_id", None)
    ss.pop("class", None)
    ss.pop("date", None)
    ss.pop("students", None)
    ss["delivered"] = False
    back = "t" if kind == TRANSISI else "py:" + str(year)
    label = phase if kind == TRANSISI else subject
    return _send(runtime, cid, "🌱 <b>" + _esc(label) +
                 "</b>\n\nPilih aktiviti untuk melihat isi RPH (DRAF):",
                 [[_button(r["label"][:58], "a:" + r["id"])] for r in rows]
                 + [[_button("⬅️ Kembali", back)]])


def _validated_activity(runtime, cid):
    ss = _session(runtime, cid)
    kind, year, ident, digest = (ss.get(k) for k in
                                ("kind", "year", "activity_id", "digest"))
    if not ident or ident not in ss.get("options", []):
        raise ValueError("No activity selected")
    row = engine.select(kind, year, ident, digest)
    if kind == TRANSISI and row["phase"] != ss.get("phase"):
        raise ValueError("Wrong phase")
    if kind == SELEPAS and ss.get("subject") not in row["subject_options"]:
        raise ValueError("Wrong subject")
    return ss, row


def _class_page(runtime, cid):
    ss, row = _validated_activity(runtime, cid)
    records = []
    try:
        getter = getattr(runtime, "_profile_class_records", None)
        if callable(getter):
            records = [r for r in (getter(cid) or [])
                       if isinstance(r, dict) and str(r.get("name") or "").strip()]
    except Exception:
        records = []
    # List is re-checked at selection, not trusted from an old keyboard.
    label = _esc(row["title"])
    keyboard = [
        [_button("🏫 " + str(r["name"])[:45], "c:" + str(i))]
        for i, r in enumerate(records[:15])
    ]
    keyboard.extend([
        [_button("➖ Biarkan maklumat kelas kosong", "c:x")],
        [_button("⬅️ Aktiviti Lain", "back")],
    ])
    return _send(runtime, cid, "📄 <b>" + label +
                 "</b>\n\nPilih kelas daripada Profil Guru atau biarkan "
                 "kosong untuk dilengkapkan kemudian dalam Word.", keyboard)


def _date_page(runtime, cid):
    ss, _ = _validated_activity(runtime, cid)
    return _send(runtime, cid,
                 "📅 <b>Tarikh RPH Aktiviti Khas</b>\n\n"
                 "Kelas: <b>" + _esc(ss.get("class") or "Belum diisi") +
                 "</b>\n\nPilih tarikh hari ini (waktu Malaysia) atau "
                 "biarkan kosong. Masa mula/tamat boleh dilengkapkan dalam "
                 "Word, atau gunakan borang Web untuk maklumat penuh.",
                 [[_button("📅 Tarikh Hari Ini", "d:t")],
                  [_button("➖ Biarkan Tarikh Kosong", "d:x")],
                  [_button("⬅️ Pilih Kelas", "class")]])


def _preview_page(runtime, cid):
    ss, row = _validated_activity(runtime, cid)
    subject = ss.get("subject") if ss["kind"] == SELEPAS else None
    details = engine.preview(ss["kind"], ss["year"], row["id"],
                             ss["digest"], subject=subject)
    phases = details.get("phases") or []
    snippets = "\n".join("• <b>" + _esc(p["label"]) + "</b>: " +
                         _esc(p["activity"][:220]) +
                         ("…" if len(p["activity"]) > 220 else "")
                         for p in phases)
    date_value = ss.get("date") or "Belum diisi"
    return _send(
        runtime, cid,
        "📄 <b>" + _esc(row["title"]) + "</b> • Tahun " + str(ss["year"]) +
        "\nSubjek/Fasa: " + _esc(subject or ss.get("phase")) +
        "\nKelas: " + _esc(ss.get("class") or "Belum diisi") +
        "\nTarikh: " + _esc(date_value) +
        "\nMasa: Belum diisi\n\n"
        "<b>Objektif:</b> " + _esc(details["objective"][:380]) +
        "\n<b>Ringkasan aktiviti:</b>\n" + snippets +
        "\n<b>BBM:</b> " + _esc(details["bbm"][:300]) +
        "\n\n⚠️ <b>DRAF UNTUK SEMAKAN GURU</b> — bukan SK/SP rasmi. "
        "Satu janaan RPH sahaja digunakan apabila fail pertama berjaya dihantar; "
        "Word dan PDF untuk pilihan yang sama tidak menggunakan dua janaan.",
        [[_button("📘 RPH Word (DRAF)", "w")],
         [_button("📕 RPH PDF (DRAF)", "f")],
         [_button("✏️ Tukar Kelas / Tarikh", "class")],
         [{"text": "🌐 Lengkapkan Masa di Web", "url": WEB_URL}],
         [_button("⬅️ Pilih Aktiviti Lain", "back")]],
    )


def _deliver(runtime, cid, fmt):
    ss, row = _validated_activity(runtime, cid)
    if "date" not in ss or "class" not in ss:
        return _class_page(runtime, cid)
    if ss.get("_busy"):
        return _send(runtime, cid, "⏳ Permintaan ini sedang diproses. Jangan tekan dua kali.",
                     [[_button("📄 Papar Semula RPH", "review")]])
    ss["_busy"] = True
    state = runtime.state.setdefault(cid, {})
    delivery_key = (ss.get("kind"), ss.get("year"), row["id"], ss.get("digest"),
                    ss.get("subject"), ss.get("class", ""), ss.get("date", ""))
    new_generation = ss.get("_confirmed_delivery_key") != delivery_key
    try:
        if new_generation:
            # The native, fail-closed access gate. No debit occurs here.
            if not runtime._credit_gate(cid, dict(state, task="rph")):
                return None
        subject = ss.get("subject") if ss["kind"] == SELEPAS else None
        metadata = {"class": ss.get("class", ""), "date": ss.get("date", ""),
                    "time": "", "students": ss.get("students", "")}
        content = engine.render(row, ss["year"], metadata, fmt, subject=subject)
        expected = b"PK" if fmt == "word" else b"%PDF-"
        if not isinstance(content, bytes) or not content.startswith(expected) or len(content) < 900:
            raise engine.SourceUnavailable("Invalid output document")
        suffix = ".docx" if fmt == "word" else ".pdf"
        with tempfile.TemporaryDirectory(prefix="cikgulaju_aktiviti_khas_") as tmp:
            target = Path(tmp) / ("CikguLaju_Aktiviti_Khas_%s_Tahun_%s_DRAF%s" %
                                  (row["id"], ss["year"], suffix))
            target.write_bytes(content)
            # Do NOT pass the word RPH in caption; legacy RPH-specific
            # send_document wrappers may mutate ordinary Lesson history.
            result = runtime.send_document(
                cid, str(target),
                "Aktiviti Khas %s Tahun %s — DRAF untuk semakan guru" %
                (row["id"], ss["year"]))
        if not runtime._telegram_delivery_ok_v25279(result):
            raise RuntimeError("Telegram delivery not confirmed")
        if new_generation:
            ss["delivered"] = True
            ss["_confirmed_delivery_key"] = delivery_key
            # This is the SAME Supabase success-only trial debit as ordinary RPH.
            runtime._consume_free_after_success_v25282(
                cid, "successful_special_activity_rph_delivery")
        return _send(runtime, cid,
                     "✅ <b>Fail DRAF berjaya dihantar.</b>\n"
                     "Muat turun format satu lagi tanpa janaan tambahan. "
                     "Semak dan sesuaikan RPH sebelum digunakan di sekolah.",
                     [[_button("📘 Word", "w"), _button("📕 PDF", "f")],
                      [_button("🌱 Aktiviti Lain", "back")],
                      [{"text": "🏠 Menu Utama", "callback_data": "home"}]])
    except Exception as exc:
        print("TELEGRAM SPECIAL RPH DELIVERY FAILED:",
              type(exc).__name__, flush=True)
        return _error(runtime, cid,
                      "Word/PDF tidak dapat disediakan atau dihantar. "
                      "Baki percubaan tidak dipotong jika penghantaran gagal.")
    finally:
        if new_generation:
            state.pop("_free_generation_pending_v25282", None)
        ss["_busy"] = False


def _handle(runtime, cid, data):
    try:
        code = data[len(PREFIX):]
        if code == "home":
            runtime.state.setdefault(cid, {}).pop("_aktiviti_khas_20261110", None)
            return _kind_page(runtime, cid)
        if code == "t":
            return _transition_page(runtime, cid)
        if code == "p":
            return _year_page(runtime, cid)
        if code.startswith("tf:") and code[3:] in ("0", "1"):
            _new_session(runtime, cid, TRANSISI, 1)
            return _options_page(runtime, cid, phase=PHASES[int(code[3:])])
        if code.startswith("py:") and code[3:] in tuple(str(y) for y in range(1, 7)):
            return _subject_page(runtime, cid, int(code[3:]))
        if code.startswith("ps:") and code[3:].isdigit():
            ss = _session(runtime, cid)
            idx = int(code[3:])
            if ss.get("kind") != SELEPAS or idx not in range(len(SUBJECTS)):
                raise ValueError("Invalid subject")
            return _options_page(runtime, cid, subject=SUBJECTS[idx])
        if code == "back":
            ss = _session(runtime, cid)
            if ss.get("kind") == TRANSISI:
                return _transition_page(runtime, cid)
            if ss.get("kind") == SELEPAS and ss.get("year") in range(1, 7):
                return _subject_page(runtime, cid, ss["year"])
            raise ValueError("Missing activity route")
        if code.startswith("a:"):
            ss = _session(runtime, cid)
            ident = code[2:]
            if ident not in ss.get("options", []) or len(ident) > 5:
                raise ValueError("Unknown activity")
            ss["activity_id"] = ident
            ss["delivered"] = False
            return _class_page(runtime, cid)
        if code == "class":
            return _class_page(runtime, cid)
        if code.startswith("c:"):
            ss, _ = _validated_activity(runtime, cid)
            if code == "c:x":
                ss["class"], ss["students"] = "", ""
            else:
                idx_str = code[2:]
                if not idx_str.isdigit():
                    raise ValueError("Invalid class")
                getter = getattr(runtime, "_profile_class_records", None)
                records = getter(cid) if callable(getter) else []
                records = [r for r in (records or [])
                           if isinstance(r, dict) and str(r.get("name") or "").strip()][:15]
                idx = int(idx_str)
                if idx not in range(len(records)):
                    raise ValueError("Old class selection")
                ss["class"] = str(records[idx]["name"])[:40]
                count = records[idx].get("students")
                ss["students"] = str(count) if isinstance(count, int) and 1 <= count <= 200 else ""
            ss["delivered"] = False
            return _date_page(runtime, cid)
        if code.startswith("d:"):
            ss, _ = _validated_activity(runtime, cid)
            if "class" not in ss or code not in ("d:t", "d:x"):
                raise ValueError("Missing class or invalid date")
            ss["date"] = (datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date().isoformat()
                          if code == "d:t" else "")
            ss["delivered"] = False
            return _preview_page(runtime, cid)
        if code == "review":
            return _preview_page(runtime, cid)
        if code in ("w", "f"):
            return _deliver(runtime, cid, "word" if code == "w" else "pdf")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print("TELEGRAM SPECIAL RPH SELECTION REJECTED:",
              type(exc).__name__, flush=True)
        return _error(runtime, cid)
    return _error(runtime, cid)


def install(runtime):
    """Install after all prior Telegram menus and callback wrappers.

    An additional Telegram message is intentional: editing the old menu reply
    markup would silently erase member-only referral buttons inserted by an
    earlier adapter that only returned the original Telegram HTTP response.
    """
    if getattr(runtime, "CIKGULAJU_TELEGRAM_SPECIAL_RPH_MENU_ACTIVE", False):
        return True
    if not (callable(getattr(runtime, "menu", None))
            and callable(getattr(runtime, "callback", None))
            and callable(getattr(runtime, "send_document", None))
            and callable(getattr(runtime, "_credit_gate", None))
            and callable(getattr(runtime, "_consume_free_after_success_v25282", None))
            and callable(getattr(runtime, "_telegram_delivery_ok_v25279", None))
            and isinstance(getattr(runtime, "state", None), dict)):
        return False
    # Fail closed if the shared catalog cannot be checked at installation.
    engine.list_options(TRANSISI, 1)
    engine.list_subjects(SELEPAS, 1)
    old_menu, old_callback = runtime.menu, runtime.callback

    def menu(cid, show_persistent=False):
        response = old_menu(cid, show_persistent=show_persistent)
        try:
            buttons = [[_button("🌱 Buka RPH Aktiviti Khas", "home")]]
            if getattr(runtime, "CIKGULAJU_MANUAL_TODAY_RPH_ACTIVE", False):
                buttons.insert(0, [{"text": "⚡ RPH Hari Ini • Jadual Manual",
                                    "callback_data": "tm26:home"}])
            _send(runtime, cid,
                  "⚡ <b>RPH Hari Ini</b> • jadual diisi sendiri\n"
                  "🌱 <b>RPH Aktiviti Khas</b> • Transisi & Tamat Sukatan (DRAF)",
                  buttons)
        except Exception as exc:
            print("TELEGRAM SPECIAL RPH MENU WARNING:",
                  type(exc).__name__, flush=True)
        return response

    def callback(cid, data):
        if str(data or "").startswith(PREFIX):
            return _handle(runtime, cid, str(data))
        return old_callback(cid, data)

    runtime.menu = menu
    runtime.callback = callback
    runtime.CIKGULAJU_TELEGRAM_SPECIAL_RPH_MENU_ACTIVE = True
    return True
