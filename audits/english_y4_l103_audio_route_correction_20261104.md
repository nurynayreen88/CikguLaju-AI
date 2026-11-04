# English Year 4 — Lesson 103/104 audio routing correction (4 November 2026)

## Independent printed-source check

- Original **Get Smart Plus 4 Teacher's Book printed p.111 / PDF page 97**: Lesson 103, Helping out / Activity 5 (*Whose ...?*), explicitly **Class CD2 Track 26**.
- Original **Teacher's Book printed p.112 / PDF page 98**: Lesson 104, Helping out / *Our world — Help the Earth — Recycle*, requires **CD2 Track 27** for vocabulary and **CD2 Track 28** for Activity 1, corroborating existing standalone Lesson 104.
- Source RPH `rph_standalone/english/year4/lesson_103.md` likewise cites CD2 Track 26; `lesson_104.md` cites CD2 Tracks 27/28.

## Code misrouting

Actual `app.py` historical `_EN4_AUDIO_ALL_V25258` and `_EN4_AUDIO_ALL_V25259` map **three** files to Lesson 103: CD2 Tracks 26, 27 and 28. The last two belong to the following Lesson 104. This can make Lesson 103's Audio / Media action send unrelated recordings.

The existing WSGI-installed `web/english_y4_l030_audio_guard.py` is extended to trim **only** the Lesson 103 entries not matching the source-assigned CD2 Track 26 and exact already-mapped Drive file ID `1vpNkB4OWao5iPQvHzEpemQrlNiNhkX4H`. It does **not** add a Telegram route for Lesson 104, infer the spoken content, or mark the Lesson as FINAL READY.

Regression test `tests/test_english_y4_l030_audio_guard.py` covers removing the two extras, retaining the expected Lesson 103 CD2 Track 26, never auto-inserting Lesson 104, preserving all other lessons/years and blocking the still-unresolved Lesson 30 media.

## Limitations

The original printed TB/RPH reference is checked; the MP3 spoken content and exact real teacher Telegram delivery **have not been independently tested**. No changes to `app.py`, user DB, subscription/credit logic or individual RPH contents. Status is a **routing correction**, not blanket FINAL READY.
