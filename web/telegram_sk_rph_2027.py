"""Use the native Telegram class/time and credit flows for 2027 sets."""

from collections import defaultdict
from html import escape
from io import BytesIO
from pathlib import Path
from secrets import token_hex
from tempfile import TemporaryDirectory

from dlp_year2_rph import _pdf, _word
from staging.dlp.year5 import downloads as year5_dlp
from staging.dlp.year6 import render_mathematics, render_science
from staging.sains.tahun5.eksport_2027 import render_rph as render_sains_year5
from staging.sains.tahun5.semakan_penjana import ReviewRuntime
from staging.sains.tahun6.eksport_2027 import render_rph as render_sains_year6
from staging.sains.tahun6.penjana_2027 import ScienceYear6Runtime

PREFIX = "sk27:"
STATE_KEY = "_sk_rph_2027"
SETS = {"s": ("Sains SK Tahun 5", "Sains", "Tahun 5"),
        "m5": ("Mathematics DLP Year 5", "Mathematics (DLP)", "Tahun 5"),
        "d5": ("Science DLP Year 5", "Science (DLP)", "Tahun 5"),
        "m": ("Mathematics DLP Year 6", "Mathematics (DLP)", "Tahun 6"),
        "s6": ("Sains SK Tahun 6", "Sains", "Tahun 6"),
        "d6": ("Science DLP Year 6", "Science (DLP)", "Tahun 6")}
FORMATS = {"word": (".docx", b"PK\x03\x04"), "pdf": (".pdf", b"%PDF-")}


def _button(text, code):
    return [{"text": text[:64], "callback_data": PREFIX + code}]


def _science_catalogue(source):
    units = defaultdict(list)
    seen = set()
    for row in source.catalog:
        code = row["pdp_sequence_code"]
        if code in seen:
            continue
        seen.add(code)
        units[row["unit_title"]].append({
            "id": code, "title": row["pdp_title"],
            "label": f"PdP {row['source_sequence_no']}",
        })
    return {f"{i:02d}": {"title": title, "lessons": lessons}
            for i, (title, lessons) in enumerate(units.items(), 1)}


def install(runtime):
    if getattr(runtime, "CIKGULAJU_SK_2027_RPH_MENU", False):
        return True
    science = {"s": (ReviewRuntime(), render_sains_year5),
               "s6": (ScienceYear6Runtime(), render_sains_year6)}
    dlp = {"m": render_mathematics, "d6": render_science,
           "m5": year5_dlp.MATHEMATICS, "d5": year5_dlp.SCIENCE}
    catalogues = {scope: _science_catalogue(source) for scope, (source, _) in science.items()}
    catalogues.update({scope: {group["id"]: group for group in module.download_catalogue()}
                       for scope, module in dlp.items()})
    old_callback = runtime.callback
    old_continue = runtime._continue_after_rph_time

    def send(cid, message, rows):
        return runtime.send(cid, message, rows + [[{"text": "🏠 Menu Utama", "callback_data": "home"}]])

    def choose_formats(cid, selection):
        return send(cid, "<b>" + escape(selection["title"]) + "</b>\nPilih format RPH.",
                    [_button("Muat turun Word", f"download:word:{selection['nonce']}"),
                     _button("Muat turun PDF", f"download:pdf:{selection['nonce']}"),
                     _button("Pilih PdP lain", f"unit:{selection['scope']}:{selection['unit']}")])

    def selected(st):
        choice = st.get(STATE_KEY)
        if choice and (st.get("subject"), st.get("year"), st.get("lesson_no")) == (
                SETS[choice["scope"]][1], SETS[choice["scope"]][2], choice["id"]):
            return choice
        return None

    def deliver(cid, st, fmt, nonce):
        choice = selected(st)
        if choice is None or choice.get("nonce") != nonce or not choice.get("session_ready"):
            raise ValueError("Select a session before downloading")
        with runtime._runtime_lock:
            if cid in runtime._processing_chats:
                return send(cid, "Permintaan ini sedang diproses.", [])
            runtime._processing_chats.add(cid)
        session = tuple(st.get(key, "") for key in (
            "rph_class", "rph_date", "rph_time", "rph_students", "rph_teacher_reflection"))
        new_generation = choice.get("confirmed_delivery") != session
        try:
            if new_generation and not runtime._credit_gate(cid, dict(st, task="rph")):
                return None
            suffix, magic = FORMATS[fmt]
            teacher = {key: st.get(f"rph_{key}") for key in ("class", "date", "time", "students")}
            teacher["reflection"] = st.get("rph_teacher_reflection")
            scope = choice["scope"]
            if scope in science:
                source, render_rph = science[scope]
                plan = source.plans[choice["id"]]
                stream = BytesIO()
                data = st if scope == "s" else teacher
                render_rph(stream, plan, _word if fmt == "word" else _pdf, teacher=data)
                content = stream.getvalue()
            else:
                module = dlp[scope]
                _, plan = module.resolve_download(choice["unit"], choice["id"])
                content = module.render_download(plan, fmt, teacher)
            if not content.startswith(magic) or len(content) < 1000:
                raise ValueError("Invalid RPH document")
            with TemporaryDirectory(prefix="cikgulaju_rph_2027_") as directory:
                path = Path(directory) / f"CikguLaju_RPH_{choice['id']}{suffix}"
                path.write_bytes(content)
                response = runtime.send_document(cid, str(path), "RPH CikguLaju 2027")
            if not runtime._telegram_delivery_ok_v25279(response):
                raise ValueError("Telegram did not confirm the document")
            if new_generation:
                choice["confirmed_delivery"] = session
                runtime._consume_free_after_success_v25282(cid, "successful_selected_rph_delivery")
            return choose_formats(cid, choice)
        except (KeyError, TypeError, ValueError, OSError, RuntimeError):
            return send(cid, "Fail RPH belum dapat dihantar.", [_button("Cuba lagi", f"download:{fmt}:{nonce}")])
        finally:
            if new_generation:
                st.pop("_free_generation_pending_v25282", None)
            with runtime._runtime_lock:
                runtime._processing_chats.discard(cid)

    def callback(cid, data):
        with runtime._runtime_lock:
            busy = cid in runtime._processing_chats and bool(runtime.state.get(cid, {}).get(STATE_KEY))
        if busy:
            return runtime.send(cid, "Fail RPH sedang dihantar.", [])
        if not isinstance(data, str) or not data.startswith(PREFIX):
            return old_callback(cid, data)
        st = runtime.state.setdefault(cid, {})
        parts = data[len(PREFIX):].split(":")
        action = parts[0]
        if parts == ["home"]:
            st.pop(STATE_KEY, None)
            return send(cid, "<b>RPH 2027</b>\nPilih set.", [
                _button(label, f"set:{key}") for key, (label, _, _) in SETS.items()])
        try:
            if action == "download" and len(parts) == 3 and parts[1] in FORMATS:
                return deliver(cid, st, parts[1], parts[2])
            scope = parts[1]
            units = catalogues[scope]
            if action == "set" and len(parts) == 2:
                st[STATE_KEY] = {"scope": scope}
                return send(cid, "<b>" + escape(SETS[scope][0]) + "</b>\nPilih unit.",
                            [_button(unit["title"], f"unit:{scope}:{key}") for key, unit in units.items()]
                            + [_button("Pilih set", "home")])
            choice = st.get(STATE_KEY, {})
            if choice.get("scope") != scope:
                raise ValueError("Wrong curriculum set")
            unit_id = parts[2]
            unit = units[unit_id]
            if action == "unit" and len(parts) == 3:
                st[STATE_KEY] = {"scope": scope, "unit": unit_id}
                return send(cid, "<b>" + escape(unit["title"]) + "</b>\nPilih Lesson/PdP.",
                            [_button(row["label"].split(" · ", 1)[0] + " • " + row["title"],
                                     f"pick:{scope}:{unit_id}:{row['id']}") for row in unit["lessons"]]
                            + [_button("Pilih unit", f"set:{scope}")])
            if action != "pick" or len(parts) != 4 or choice.get("unit") != unit_id:
                raise ValueError("Wrong unit")
            lesson = next((r for r in unit["lessons"] if r["id"] == parts[3]), None)
            if lesson is None:
                raise ValueError("Unknown lesson")
            _, subject, year = SETS[scope]
            runtime.state[cid] = {
                "task": "quick_material", "quick_material_flow": True, "_cid": cid,
                "assessment_mode": "formative", "year": year, "year_label": year,
                "subject": subject, "unit": unit["title"], "unit_title": unit["title"],
                "topic": lesson["title"], "lesson_no": lesson["id"],
                STATE_KEY: {"scope": scope, "unit": unit_id, "nonce": token_hex(6), **lesson},
            }
            return runtime._lesson_to_class_v2439(cid)
        except (KeyError, TypeError, ValueError, IndexError):
            return send(cid, "Pilihan RPH 2027 tidak sah. Pilih semula.", [_button("RPH 2027", "home")])

    def after_time(cid, st):
        choice = selected(st)
        if choice is None:
            return old_continue(cid, st)
        choice["session_ready"] = True
        return choose_formats(cid, choice)

    runtime.callback = callback
    runtime._continue_after_rph_time = after_time
    runtime.CIKGULAJU_SK_2027_RPH_MENU = True
    return True
