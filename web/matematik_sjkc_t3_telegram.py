"""Use reviewed school Mathematics sources in Telegram's regular RPH workflow."""

from html import escape
import logging
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from curriculum_version_selector import LEGACY
from staging.matematik_sjkc.tahun_3.rph import (
    SUBJECT, YEAR, enabled, lessons, render, resolve, units,
)

MATERIAL_FORMATS = {"rph": "pdf", "rph_word": "word"}


def install(runtime):
    return install_school_math(
        runtime, SimpleNamespace(SUBJECT=SUBJECT, YEAR=YEAR, enabled=enabled, units=units,
                                 lessons=lessons, resolve=resolve, render=render),
        "sjkc3", "MATEMATIK_SJKC_T3_RPH_ACTIVE",
    )


def install_school_math(runtime, source, key, active_attr, *, slot_picker=None, slot_valid=None):
    if not source.enabled():
        return False
    if getattr(runtime, active_attr, False):
        return True
    subject, year_label = source.SUBJECT, f"Tahun {source.YEAR}"
    pick_subject = "sub_" + subject
    unit_prefix, pdp_prefix = f"m{key}u:", f"m{key}p:"
    unit_key, retry_key = f"{key}_unit", f"_{key}_partial_delivery"
    credit_reason = f"successful_{key[:-1]}_rph_delivery"
    previous_callback = runtime.callback
    previous_available = runtime._available_materials_v2528
    previous_submit = runtime._submit_materials_v2528
    subject_list = runtime.SUBJECTS_BY_GRADE.get(year_label)
    if not isinstance(subject_list, list):
        return False
    try:
        source.units()
    except (OSError, ValueError, KeyError):
        logging.getLogger(__name__).exception("%s source unavailable", subject)
        return False
    if subject not in subject_list:
        subject_list.append(subject)

    def in_flow(state):
        return (state.get("year") == year_label
                and state.get("curriculum_version", LEGACY) == LEGACY
                and state.get("task") in ("quick_material", "rph"))

    def selected(state):
        if not in_flow(state) or state.get("subject") != subject:
            return None
        return source.resolve(state.get(unit_key), state.get("pdp_no"))

    def show_units(cid, state):
        state.update(subject=subject, pdp_no=None)
        state[unit_key] = None
        state.pop(retry_key, None)
        back = ({"text": "⬅️ RPH Hari Ini", "callback_data": "todayrph272"}
                if state.get(f"_{key}_today_slot") else
                {"text": "⬅️ Pilih Subjek", "callback_data": "back_subjects"})
        return runtime.send(cid, f"<b>{subject} · {year_label}</b>\nPilih unit.", [
            *[[{"text": f"Unit {number} · {label}", "callback_data": unit_prefix + str(number)}]
              for number, label in source.units()],
            [back],
        ])

    def callback(cid, data):
        if not isinstance(data, str) or (data != pick_subject and not data.startswith((unit_prefix, pdp_prefix))):
            return previous_callback(cid, data)
        state = runtime.state.setdefault(cid, {})
        if not in_flow(state):
            return runtime.send(cid, f"Sila pilih KSSR → {year_label} → {subject} semula.")
        if data == pick_subject:
            state.pop(f"_{key}_today_slot", None)
            return show_units(cid, state)
        if state.get("subject") != subject:
            return runtime.send(cid, f"Sila pilih {subject} semula.")
        prefix, value = data.split(":", 1)
        if not re.fullmatch(r"[1-9][0-9]?", value):
            return show_units(cid, state)
        number = int(value)
        if prefix == unit_prefix[:-1]:
            rows = [row for row in source.lessons() if row["unit_number"] == number]
            if not rows:
                return show_units(cid, state)
            state.update(pdp_no=None)
            state[unit_key] = number
            state.pop(retry_key, None)
            return runtime.send(cid, f"<b>{escape(rows[0]['unit'])}</b>\nPilih PdP.", [
                *[[{"text": f"PdP {row['pdp']:03} · {row['topic']}",
                    "callback_data": pdp_prefix + str(row["pdp"])}] for row in rows],
                [{"text": "⬅️ Pilih Unit", "callback_data": (
                    unit_prefix + "0" if state.get(f"_{key}_today_slot") else pick_subject
                )}],
            ])
        row = source.resolve(state.get(unit_key), number)
        if row is None:
            return show_units(cid, state)
        if state.get("pdp_no") != number:
            state.pop(retry_key, None)
        state.update(lesson=str(number), lesson_no=str(number), pdp_no=number,
                     unit=row["unit"], topic=row["topic"], rph_mode="fast_rpt")
        if slot_picker and state.get(f"_{key}_today_slot") is not None:
            return slot_picker(runtime, cid)
        return runtime._lesson_to_class_v2439(cid)

    def available(state):
        if state.get("subject") != subject:
            return previous_available(state)
        return list(MATERIAL_FORMATS) if selected(state) else []

    def submit(cid):
        state = runtime.state.setdefault(cid, {})
        if state.get("subject") != subject:
            return previous_submit(cid)
        row = selected(state)
        if row is None:
            return runtime.send(cid, f"Sila pilih Unit dan PdP {subject} semula.")
        if slot_valid and state.get(f"_{key}_today_slot") and not slot_valid(runtime, cid):
            return runtime.send(cid, "Slot telah berubah. Pilih semula melalui RPH Hari Ini.")
        requested = state.get("_materials_selected_v2528") or ()
        formats = [fmt for material, fmt in MATERIAL_FORMATS.items() if material in requested]
        if not formats:
            return runtime._material_picker_v2528(cid, "Sila pilih RPH Word atau PDF.")
        with runtime._runtime_lock:
            if cid in runtime._processing_chats:
                return runtime.send(cid, "Fail sedang disediakan. Sila tunggu sebentar.")
            runtime._processing_chats.add(cid)
        pending = "_free_generation_pending_v25282"
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
            with TemporaryDirectory(prefix=f"cikgulaju-{key}-") as tmp:
                files = {}
                for fmt in formats:
                    if fmt in delivered:
                        continue
                    name, content = source.render(row, fmt, teacher)
                    path = Path(tmp) / name
                    path.write_bytes(content)
                    files[fmt] = path
                for fmt, path in files.items():
                    result = runtime.send_document(cid, str(path), f"RPH {subject} · PdP {row['pdp']:03}")
                    if not runtime._telegram_delivery_ok_v25279(result):
                        raise RuntimeError("Telegram delivery not confirmed")
                    first = not delivered
                    delivered.add(fmt)
                    state[retry_key] = (selection, delivered)
                    if first:
                        runtime._consume_free_after_success_v25282(cid, credit_reason)
            state.pop(retry_key, None)
            return result
        except Exception:
            logging.getLogger(__name__).exception("%s delivery failed", subject)
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
    setattr(runtime, active_attr, True)
    if slot_picker:
        setattr(runtime, f"_{key}_open_units", show_units)
    return True
