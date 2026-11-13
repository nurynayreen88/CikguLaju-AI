"""Present RPH Harian and RPH Aktiviti Khas inside Telegram's Sediakan RPH.

Display-only adapter for the existing 'quick' entry. It does not change
curriculum navigation, callbacks, material submit, credits or document engines.
Install after the Special Activity RPH adapter is active.
"""
from __future__ import annotations


def install(runtime):
    if getattr(runtime, "CIKGULAJU_RPH_ENTRY_CHOICES_20261110", False):
        return True
    if not (callable(getattr(runtime, "quick", None))
            and callable(getattr(runtime, "send", None))
            and isinstance(getattr(runtime, "state", None), dict)
            and getattr(runtime, "CIKGULAJU_TELEGRAM_SPECIAL_RPH_MENU_ACTIVE", False)):
        return False

    def quick(cid):
        # Preserve the previous entry's exact state initialization. RPH Harian
        # still opens choose_grade, then all existing class/date/time/material
        # selection callbacks, ending at matsubmit2528, without any rerouting.
        runtime.state[cid] = {
            "task": "quick_material",
            "quick_material_flow": True,
            "_cid": cid,
        }
        return runtime.send(
            cid,
            "📚 <b>Sediakan RPH</b>\n\n"
            "📝 <b>RPH Harian</b>\n"
            "Bahan Bahasa Inggeris mengikut kurikulum Sekolah Kebangsaan (SK). "
            "Untuk pengajaran biasa mengikut kurikulum. Pilih "
            "<b>Tahun/Tingkatan → Subjek → Tema/Unit/Tajuk → Lesson/PdP</b>. "
            "SK/SP, RPT/SOW, buku teks dan buku aktiviti dipadankan secara "
            "automatik apabila sumber tersedia. Selepas memilih kelas, "
            "tarikh dan masa, pilih bahan yang diperlukan dan tekan "
            "<b>✅ SUBMIT</b>.\n\n"
            "🌱 <b>RPH Aktiviti Khas</b>\n"
            "Untuk Minggu Transisi Tahun 1 atau aktiviti selepas tamat "
            "sukatan. Pilih aktiviti yang sesuai dan muat turun Word/PDF. "
            "<b>Bahan aktiviti khas masih DRAF untuk semakan guru.</b>",
            [
                [{"text": "📝 RPH Harian", "callback_data": "choose_grade"}],
                [{"text": "🌱 RPH Aktiviti Khas", "callback_data": "ak26:home"}],
                [{"text": "🏠 Menu Utama", "callback_data": "home"}],
            ],
        )

    runtime.quick = quick
    runtime.CIKGULAJU_RPH_ENTRY_CHOICES_20261110 = True
    return True
