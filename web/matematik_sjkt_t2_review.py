"""Catalog and Telegram admin review flow for Matematik SJKT Tahun 2."""

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

from pymupdf import FileDataError

from audits.matematik_sjkt_tahun_2.eksport_rph import lessons, render, resolve

YEAR = 2
TITLE = "Matematik SJKT Tahun 2"
UNIT_NAMES = (
    "Nombor bulat", "Operasi asas", "Pecahan dan perpuluhan", "Wang",
    "Masa dan waktu", "Ukuran dan sukatan", "Ruang", "Pengurusan data",
)
FORMATS = {"word": "docx", "pdf": "pdf"}
RENDER_ERRORS = (OSError, ValueError, KeyError, BadZipFile, FileDataError)
CALLBACK = "admin_sjkt2"
BUTTON = {"text": "Semak RPH Matematik SJKT Tahun 2", "callback_data": CALLBACK}


def options(unit=None):
    if unit is None:
        return [
            {"value": number, "label": f"Unit {number} · {name}"}
            for number, name in enumerate(UNIT_NAMES, 1)
        ]
    return [
        {
            "value": row["pdp"],
            "label": f"PdP {row['pdp']:03} · {row['tajuk_tamil']}",
            "sp": row["sp"],
            "buku_teks": row["buku_teks"],
            "buku_aktiviti": row["buku_aktiviti"],
        }
        for row in lessons() if row["unit"] == unit
    ]


def install(runtime):
    previous = runtime.callback

    def callback(cid, data):
        if not isinstance(data, str) or (data != CALLBACK and not data.startswith(CALLBACK + ":")):
            return previous(cid, data)
        if not runtime._is_admin(cid):
            return runtime.send(cid, "Akses admin diperlukan.")

        def button(label, suffix):
            return [{"text": label, "callback_data": f"{CALLBACK}{suffix}"}]

        parts = data.split(":")
        if len(parts) == 1:
            return runtime.send(cid, f"<b>Semakan RPH {TITLE}</b>\nPilih unit.", [
                *[button(row["label"], f":{row['value']}") for row in options()],
                [{"text": "Kembali ke Panel Admin", "callback_data": "admin_panel"}],
            ])

        if len(parts) not in (2, 3, 4) or parts[1] not in tuple(map(str, range(1, 9))):
            return runtime.send(cid, "Pilihan unit tidak sah.")
        unit = int(parts[1])
        if len(parts) == 2:
            return runtime.send(cid, "Pilih PdP untuk semakan.", [
                *[button(row["label"], f":{unit}:{row['value']}") for row in options(unit)],
                button("Kembali ke unit", ""),
            ])
        pdp = parts[2]
        if not pdp.isascii() or not pdp.isdecimal() or not 1 <= len(pdp) <= 2:
            return runtime.send(cid, "Pilihan PdP tidak sah.")
        pdp = int(pdp)
        if resolve(unit, pdp) is None:
            return runtime.send(cid, "PdP tiada dalam unit yang dipilih.")
        if len(parts) == 3:
            return runtime.send(cid, f"PdP {pdp:03} · Pilih format RPH.", [
                button("Word", f":{unit}:{pdp}:word"),
                button("PDF", f":{unit}:{pdp}:pdf"),
                button("Kembali ke PdP", f":{unit}"),
            ])
        extension = FORMATS.get(parts[3])
        if extension is None:
            return runtime.send(cid, "Format RPH tidak sah.")
        try:
            name, document = render(unit, pdp, extension)
            with TemporaryDirectory(prefix="cikgulaju-sjkt-review-") as directory:
                path = Path(directory, name)
                path.write_bytes(document)
                result = runtime.send_document(cid, str(path), f"Semakan RPH {TITLE} · PdP {pdp:03}")
            if runtime._telegram_delivery_ok_v25279(result):
                return result
        except RENDER_ERRORS:
            runtime.app.logger.exception("Matematik SJKT review export failed")
        return runtime.send(cid, "Fail semakan belum dapat dihantar. Sila cuba semula.")

    runtime.callback = callback
    runtime.MATEMATIK_SJKT_T2_REVIEW_BUTTON = BUTTON
