"""Use the shared Matematik SJKC source in Telegram's regular RPH workflow."""

from html import escape
import logging
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from curriculum_version_selector import LEGACY
from staging.matematik_sjkc.tahun_3.rph import (
    SUBJECT, YEAR, enabled, lessons, render, resolve, units,
)

YEAR_LABEL = f"Tahun {YEAR}"
PICK_SUBJECT = "sub_" + SUBJECT
UNIT_PREFIX = "msjkc3u:"
PDP_PREFIX = "msjkc3p:"
MATERIAL_FORMATS = {"rph": "pdf", "rph_word": "word"}


def install(runtime):
    if not enabled():
        return False
    if getattr(runtime, "MATEMATIK_SJKC_T3_RPH_ACTIVE", False):
        return True
    previous_callback = runtime.callback
    previous_available = runtime._available_materials_v2528
    previous_submit = runtime._submit_materials_v2528
    subject_list = runtime.SUBJECTS_BY_GRADE.get(YEAR_LABEL)
    if not isinstance(subject_list, list):
        return False
    try:
        units()
    except (OSError, ValueError, KeyError):
        logging.getLogger(__name__).exception("Matematik SJKC source unavailable")
        return False
    if SUBJECT not in subject_list:
        subject_list.append(SUBJECT)

    def in_flow(state):
        return (state.get("year") == YEAR_LABEL
                and state.get("curriculum_version", LEGACY) == LEGACY
                and state.get("task") in ("quick_material", "rph"))

    def selected(state):
        if not in_flow(state) or state.get("subject") != SUBJECT:
            return None
        return resolve(state.get("sjkc3_unit"), state.get("pdp_no"))

    def show_units(cid, state):
        state.update(subject=SUBJECT, sjkc3_unit=None, pdp_no=None)
        state.pop("_sjkc3_partial_delivery", None)
        return runtime.send(cid, f"<b>{SUBJECT} · {YEAR_LABEL}</b>\nPilih unit.", [
            *[[{"text": f"Unit {number} · {label}", "callback_data": UNIT_PREFIX + str(number)}]
              for number, label in units()],
            [{"text": "⬅️ Pilih Subjek", "callback_data": "back_subjects"}],
        ])

    def callback(cid, data):
        if not isinstance(data, str) or (data != PICK_SUBJECT and not data.startswith((UNIT_PREFIX, PDP_PREFIX))):
            return previous_callback(cid, data)
        state = runtime.state.setdefault(cid, {})
        if not in_flow(state):
            return runtime.send(cid, "Sila pilih KSSR → Tahun 3 → Matematik SJKC semula.")
        if data == PICK_SUBJECT:
            return show_units(cid, state)
        if state.get("subject") != SUBJECT:
            return runtime.send(cid, "Sila pilih Matematik SJKC semula.")
        prefix, value = data.split(":", 1)
        if not re.fullmatch(r"[1-9][0-9]?", value):
            return show_units(cid, state)
        number = int(value)
        if prefix == UNIT_PREFIX[:-1]:
            rows = [row for row in lessons() if row["unit_number"] == number]
            if not rows:
                return show_units(cid, state)
            state.update(sjkc3_unit=number, pdp_no=None)
            state.pop("_sjkc3_partial_delivery", None)
            return runtime.send(cid, f"<b>{escape(rows[0]['unit'])}</b>\nPilih PdP.", [
                *[[{"text": f"PdP {row['pdp']:03} · {row['topic']}",
                    "callback_data": PDP_PREFIX + str(row["pdp"])}] for row in rows],
                [{"text": "⬅️ Pilih Unit", "callback_data": PICK_SUBJECT}],
            ])
        row = resolve(state.get("sjkc3_unit"), number)
        if row is None:
            return show_units(cid, state)
        if state.get("pdp_no") != number:
            state.pop("_sjkc3_partial_delivery", None)
        state.update(lesson=str(number), lesson_no=str(number), pdp_no=number,
                     unit=row["unit"], topic=row["topic"], rph_mode="fast_rpt")
        return runtime._lesson_to_class_v2439(cid)

    def available(state):
        if state.get("subject") != SUBJECT:
            return previous_available(state)
        return list(MATERIAL_FORMATS) if selected(state) else []

    def submit(cid):
        state = runtime.state.setdefault(cid, {})
        if state.get("subject") != SUBJECT:
            return previous_submit(cid)
        row = selected(state)
        if row is None:
            return runtime.send(cid, "Sila pilih Unit dan PdP Matematik SJKC semula.")
        requested = state.get("_materials_selected_v2528") or ()
        formats = [fmt for material, fmt in MATERIAL_FORMATS.items() if material in requested]
        if not formats:
            return runtime._material_picker_v2528(cid, "Sila pilih RPH Word atau PDF.")
        with runtime._runtime_lock:
            if cid in runtime._processing_chats:
                return runtime.send(cid, "Fail sedang disediakan. Sila tunggu sebentar.")
            runtime._processing_chats.add(cid)
        pending = "_free_generation_pending_v25282"
        retry_key = "_sjkc3_partial_delivery"
        teacher = {
            "class": str(state.get("rph_class") or ""),
            "date": str(state.get("rph_date") or ""),
            "time": str(state.get("rph_time") or ""),
            "students": str(state.get("rph_students") or state.get("student_count") or ""),
            "reflection": str(state.get("rph_teacher_reflection") or ""),
        }
        selection = (row["pdp"], tuple(teacher.values()), tuple(formats))
        previous, delivered = state.get(retry_key, (None, set()))
        if previous != selection:
            delivered = set()
            state.pop(retry_key, None)
        try:
            state.pop(pending, None)
            if not delivered and not runtime._credit_gate(cid, dict(state, task="rph")):
                return None
            with TemporaryDirectory(prefix="cikgulaju-sjkc-") as tmp:
                files = {}
                for fmt in formats:
                    if fmt in delivered:
                        continue
                    name, content = render(row, fmt, teacher)
                    path = Path(tmp) / name
                    path.write_bytes(content)
                    files[fmt] = path
                for fmt, path in files.items():
                    result = runtime.send_document(cid, str(path), f"RPH {SUBJECT} · PdP {row['pdp']:03}")
                    if not runtime._telegram_delivery_ok_v25279(result):
                        raise RuntimeError("Telegram delivery not confirmed")
                    first = not delivered
                    delivered.add(fmt)
                    state[retry_key] = (selection, delivered)
                    if first:
                        runtime._consume_free_after_success_v25282(cid, "successful_sjkc_rph_delivery")
            state.pop(retry_key, None)
            return result
        except Exception:
            logging.getLogger(__name__).exception("Matematik SJKC delivery failed")
            message = ("Sebahagian fail berjaya dihantar. Tekan SUBMIT untuk cuba format yang belum dihantar."
                       if delivered else "RPH belum berjaya dihantar. Sila cuba semula.")
            return runtime.send(cid, message)
        finally:
            state.pop(pending, None)
            with runtime._runtime_lock:
                runtime._processing_chats.discard(cid)

    runtime.callback = callback
    runtime._available_materials_v2528 = available
    runtime._submit_materials_v2528 = submit
    runtime.MATEMATIK_SJKC_T3_RPH_ACTIVE = True
    return True
