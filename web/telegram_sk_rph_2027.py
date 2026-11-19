"""Use the native Telegram class/time and credit flows for 2027 sets."""

from collections import defaultdict
from html import escape
from io import BytesIO
from pathlib import Path
from secrets import token_hex
from tempfile import TemporaryDirectory

from dlp_year2_rph import _pdf, _word
from staging.dlp.year3 import render_mathematics as year3_math, render_science as year3_science
from staging.dlp.year4 import render_mathematics as year4_math, render_science as year4_science
from staging.dlp.year5 import downloads as year5_dlp
from staging.dlp.year6 import render_mathematics, render_science
from staging.matematik.documents_2027 import Downloads as MathSKDownloads
from staging.sains.tahun5.eksport_2027 import render_rph as render_sains_year5
from staging.sains.tahun5.semakan_penjana import ReviewRuntime
from staging.sains.tahun6.eksport_2027 import render_rph as render_sains_year6
from staging.sains.tahun6.penjana_2027 import ScienceYear6Runtime
from web.math_y6_ratio_source_hold_20261110 import reviewed_math_y6_unit

PREFIX = "sk27:"
STATE_KEY = "_sk_rph_2027"
SETS = {"d3": ("Science DLP Year 3", "Science (DLP)", "Tahun 3"),
        "m3": ("Mathematics DLP Year 3", "Mathematics (DLP)", "Tahun 3"),
        "d4": ("Science DLP Year 4", "Science (DLP)", "Tahun 4"),
        "m4": ("Mathematics DLP Year 4", "Mathematics (DLP)", "Tahun 4"),
        "s": ("Sains SK Tahun 5", "Sains", "Tahun 5"),
        "dp2": ("Matematik SK Tahun 2 · DPK Edisi 3", "Matematik", "Tahun 2"),
        "dp3": ("Matematik SK Tahun 3 · DPK Edisi 3", "Matematik", "Tahun 3"),
        "mt4": ("Matematik SK Tahun 4", "Matematik", "Tahun 4"),
        "mt5": ("Matematik SK Tahun 5", "Matematik", "Tahun 5"),
        "mt6": ("Matematik SK Tahun 6", "Matematik", "Tahun 6"),
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
    documents = {"d3": year3_science, "m3": year3_math,
                 "d4": year4_science, "m4": year4_math, "m": render_mathematics, "d6": render_science,
                 "m5": year5_dlp.MATHEMATICS, "d5": year5_dlp.SCIENCE,
                 "mt4": MathSKDownloads(4), "mt5": MathSKDownloads(5), "mt6": MathSKDownloads(6),
                 "dp2": MathSKDownloads(2, dpk=True), "dp3": MathSKDownloads(3, dpk=True)}
    catalogues = {scope: _science_catalogue(source) for scope, (source, _) in science.items()}
    catalogues.update({scope: {group["id"]: group for group in module.download_catalogue()}
                       for scope, module in documents.items()})
    old_callback = runtime.callback
    old_continue = runtime._continue_after_rph_time

    def send(cid, message, rows):
        return runtime.send(cid, message, rows + [[{"text": "🏠 Menu Utama", "callback_data": "home"}]])

    def choose_formats(cid, selection):
        return send(cid, "<b>" + escape(selection["title"]) + "</b>\nPilih format RPH.",
                    [_button("Muat turun Word", f"download:word:{selection['nonce']}"),
                     _button("Muat turun PDF", f"download:pdf:{selection['nonce']}"),
                     _button("Pilih PdP lain", f"unit:{selection['scope']}:{selection['unit']}")])

    def legacy_math_unit(st):
        if st.get("year") == "Tahun 6" and st.get("subject") == "Matematik":
            return reviewed_math_y6_unit(6, "MATH", st.get("pdp_sequence_code"))
        return None

    def send_reviewed_math_unit(cid, st, unit):
        st[STATE_KEY] = {"scope": "mt6"}
        title = escape(catalogues["mt6"][unit]["title"])
        return send(cid, f"Pilih Lesson Matematik SK Tahun 6 dalam <b>{title}</b>.",
                    [_button(f"Buka Unit {int(unit)} · RPH 2027", f"unit:mt6:{unit}")])

    def selected(st):
        choice = st.get(STATE_KEY)
        if choice and "id" in choice and (st.get("subject"), st.get("year"), st.get("lesson_no")) == (
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
                module = documents[scope]
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
        st = runtime.state.get(cid, {})
        if data == "matsubmit2528" and (unit := legacy_math_unit(st)):
            return send_reviewed_math_unit(cid, st, unit)
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
            if action in ("set", "dlp") and len(parts) == 2:
                _, subject, year = SETS[scope]
                curriculum = st.get("curriculum_version")
                if action == "dlp":
                    if curriculum != "dlp" or st.get("year") != year or not subject.endswith(" (DLP)"):
                        raise ValueError("Wrong DLP curriculum or year")
                    back = [{"text": "Pilih Subjek DLP", "callback_data": f"cv_year{year.split()[-1]}_dlp"}]
                else:
                    back = _button("Pilih set", "home")
                st[STATE_KEY] = {"scope": scope, "from_dlp": action == "dlp"}
                return send(cid, "<b>" + escape(SETS[scope][0]) + "</b>\nPilih unit.",
                            [_button(unit["title"], f"unit:{scope}:{key}") for key, unit in units.items()]
                            + [back])
            choice = st.get(STATE_KEY, {})
            if choice.get("scope") != scope:
                raise ValueError("Wrong curriculum set")
            unit_id = parts[2]
            unit = units[unit_id]
            if action == "unit" and len(parts) == 3:
                st[STATE_KEY] = {"scope": scope, "unit": unit_id, "from_dlp": choice.get("from_dlp", False)}
                return send(cid, "<b>" + escape(unit["title"]) + "</b>\nPilih Lesson/PdP.",
                            [_button((row["label"] if scope in ("dp2", "dp3") else row["label"].split(" · ", 1)[0])
                                     + " • " + row["title"],
                                     f"pick:{scope}:{unit_id}:{row['id']}") for row in unit["lessons"]]
                            + [_button("Pilih unit", f"{'dlp' if choice.get('from_dlp') else 'set'}:{scope}")])
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
                STATE_KEY: {"scope": scope, "unit": unit_id, "nonce": token_hex(6),
                            "from_dlp": choice.get("from_dlp", False), **lesson},
            }
            if choice.get("from_dlp"):
                runtime.state[cid]["curriculum_version"] = "dlp"
            return runtime._lesson_to_class_v2439(cid)
        except (KeyError, TypeError, ValueError, IndexError):
            return send(cid, "Pilihan RPH 2027 tidak sah. Pilih semula.", [_button("RPH 2027", "home")])

    def after_time(cid, st):
        if unit := legacy_math_unit(st):
            return send_reviewed_math_unit(cid, st, unit)
        choice = selected(st)
        if choice is None:
            return old_continue(cid, st)
        choice["session_ready"] = True
        return choose_formats(cid, choice)

    # These old pickers have already resolved the exact PdP code before
    # handing off. Keep their indexed callbacks and saved choices stable.
    def guard_picker(picker):
        def guarded(cid, *args, **kwargs):
            st = runtime.state.get(cid, {})
            if unit := legacy_math_unit(st):
                return send_reviewed_math_unit(cid, st, unit)
            return picker(cid, *args, **kwargs)
        return guarded

    runtime.callback = callback
    runtime._continue_after_rph_time = after_time
    for name in ("_temporary_auto_pack_v2386", "_lesson_to_class_v2439"):
        picker = getattr(runtime, name, None)
        if callable(picker):
            setattr(runtime, name, guard_picker(picker))
    runtime.CIKGULAJU_SK_2027_RPH_MENU = True
    return True
