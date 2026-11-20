"""Show original downloadable Music recordings in the Telegram subject menu."""
from functools import lru_cache
from html import escape
import re

from staging.pendidikan_muzik.rpt_rph_2027.external_audio_links_staging import audio_link_action
from web.telegram_provisional_arab_music_api import _music_index

SUBJECT_MENU = "devsub2617_Pendidikan Muzik"
PAGE_SIZE = 7
CHOICE = re.compile(r"muzik-audio:(menu|pdp):([2-6]):(\d{1,2})")


@lru_cache(maxsize=5)
def _available(year):
    result = []
    for row in _music_index(year):
        pdp = row["pdp"]
        links = audio_link_action(year, pdp)["links"]
        if links and all("download_url" in item for item in links):
            title = row.get("focus_pdp") or row["unit"]
            result.append((pdp, title, links))
    return tuple(result)


def install(runtime):
    if getattr(runtime, "TELEGRAM_MUSIC_SOURCE_AUDIO_ACTIVE", False):
        return True
    previous = runtime.callback

    def menu(chat_id, year, page):
        rows = _available(year)
        start = page * PAGE_SIZE
        if start >= len(rows):
            return previous(chat_id, SUBJECT_MENU)
        buttons = [[{"text": f"PdP {pdp:02d} · {title}"[:64],
                     "callback_data": f"muzik-audio:pdp:{year}:{pdp}"}]
                   for pdp, title, _ in rows[start:start + PAGE_SIZE]]
        navigation = []
        if page:
            navigation.append({"text": "⬅️ Sebelum", "callback_data": f"muzik-audio:menu:{year}:{page - 1}"})
        if start + PAGE_SIZE < len(rows):
            navigation.append({"text": "Seterusnya ➡️", "callback_data": f"muzik-audio:menu:{year}:{page + 1}"})
        if navigation:
            buttons.append(navigation)
        buttons.append([{"text": "⬅️ Pilih subjek", "callback_data": "back_subjects"}])
        return runtime.send(chat_id, f"🎵 <b>Audio Pendidikan Muzik Tahun {year}</b>\n\nPilih PdP.", buttons)

    def callback(chat_id, data):
        state = runtime.state.get(chat_id, {})
        match_year = re.fullmatch(r"Tahun ([2-6])", str(state.get("year", "")))
        if not match_year:
            return previous(chat_id, data)
        year = int(match_year[1])
        if data == SUBJECT_MENU:
            return menu(chat_id, year, 0)
        choice = CHOICE.fullmatch(str(data))
        if choice is None or int(choice[2]) != year:
            return previous(chat_id, data)
        number = int(choice[3])
        if choice[1] == "menu":
            return menu(chat_id, year, number)
        for index, (pdp, title, links) in enumerate(_available(year)):
            if pdp != number:
                continue
            buttons = [[{"text": f"⬇️ Audio {track['track']} · {track['title']}"[:64],
                         "url": track["download_url"]}] for track in links]
            buttons.append([{"text": "⬅️ Pilih PdP",
                             "callback_data": f"muzik-audio:menu:{year}:{index // PAGE_SIZE}"}])
            return runtime.send(chat_id, f"🔊 <b>PdP {pdp:02d} · {escape(title)}</b>\n\n"
                                "Pilih trek untuk memuat turun dari Google Drive sumber asal.", buttons)
        return menu(chat_id, year, 0)

    runtime.callback = callback
    runtime.TELEGRAM_MUSIC_SOURCE_AUDIO_ACTIVE = True
    return True
