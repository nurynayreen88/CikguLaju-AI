"""Show verified Music recordings in the existing Telegram subject menu."""
from staging.pendidikan_muzik.rpt_rph_2027.external_audio_links_staging import audio_link_action


SUBJECT_MENU = "devsub2617_Pendidikan Muzik"
CHOICES = {
    21: "PdP 21 · Permainan Susun Notasi",
    24: "PdP 24 · Kamu Tanya, Saya Jawab",
}
CALLBACKS = {f"muzik-audio-y4:{number}": number for number in CHOICES}


def install(runtime):
    if getattr(runtime, "TELEGRAM_MUSIC_SOURCE_AUDIO_ACTIVE", False):
        return True
    previous = runtime.callback

    def callback(chat_id, data):
        state = runtime.state.get(chat_id, {})
        if state.get("year") != "Tahun 4":
            return previous(chat_id, data)
        if data == SUBJECT_MENU:
            available = [
                [{"text": title, "callback_data": f"muzik-audio-y4:{number}"}]
                for number, title in CHOICES.items()
                if audio_link_action(4, number)["content_verified"]
            ]
            if not available:
                return previous(chat_id, data)
            return runtime.send(chat_id, "🎵 <b>Audio Pendidikan Muzik Tahun 4</b>\n\nPilih PdP.",
                                [*available, [{"text": "⬅️ Pilih subjek", "callback_data": "back_subjects"}]])
        number = CALLBACKS.get(str(data))
        if number is None:
            return previous(chat_id, data)
        audio = audio_link_action(4, number)
        back = [{"text": "⬅️ Pilih PdP", "callback_data": SUBJECT_MENU}]
        if not audio["content_verified"]:
            return runtime.send(chat_id, "Pautan audio untuk PdP ini belum dapat disahkan.", [back])
        buttons = [[{"text": f"Audio {track['track']} · {track['title']}", "url": track["url"]}]
                   for track in audio["links"]]
        return runtime.send(chat_id, f"🔊 <b>{CHOICES[number]}</b>\n\n{audio['notice']}", [*buttons, back])

    runtime.callback = callback
    runtime.TELEGRAM_MUSIC_SOURCE_AUDIO_ACTIVE = True
    return True
