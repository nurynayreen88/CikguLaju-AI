# English Year 4 — full legacy Telegram audio-route inventory, 4 Nov 2026

**Source:** Automated Python 3.12 read-only extraction of `_EN4_AUDIO_ALL_V25259` from the actual `app.py`, cross-checked against the instructional portion of **160/160** standalone English Year 4 lesson files. CI workflow `English 2–6 native PDF core and Year4 audio conflict evidence`, successful audit run `41802175950`, artifact `english-y4-legacy-audio-route-audit-20261104`.

## Full inventory

| Status | Media rows |
|---|---:|
| Explicit matching instructional CD/Track reference | 52 |
| No explicit instructional CD/Track reference in the parsed segment | 14 |
| Potential wrong disc (Year4 L030) | 1 |
| Potential extra/wrong track (Year4 L103) | 2 |
| **Total routed audio files** | **69** |

**56** distinct Lessons have historical routed files. **104** have no route in this specific legacy map; that does not prove they have no audio or alternative media. The parser recognizes an abbreviated paired instruction such as `CD1 Track 26 and Track 37`, so **Lesson 27 is not classified as an error**.

## Source-confirmed potential mismatches

- **Lesson 30:** historical **CD2 Track29** conflicts with original TB p39 **CD1 Track29** for Student's Book p20 Activity2. Two distinct MP3 assets exist, but speech content remains unverified. Production safety guard blocks L030 media pending verification.
- **Lesson 103:** historical **CD2 Tracks26, 27, 28** includes tracks belonging to the following Lesson 104. Original Teacher's Book printed pp111–112 and standalone RPH give L103 **CD2 Track26** and L104 **CD2 Tracks27/28**. The separate source-scoped fix in PR #210 trims L103 extras while leaving L104 activation pending, subject to CI.

## Remaining source checks

The 14 routes with no explicit parsed instructional reference **are not automatically erroneous**. Their exact audio identity, correct lesson activity, actual spoken recording, teacher access and Telegram delivery require independent verification. A reference-number match alone is not a FINAL READY approval.

**Scope safety:** No actual MP3, app.py, user database, payment, quota, Telegram callback or RPH content was changed by this audit. The per-Lesson route ledger is an output artifact, not a production lookup table.
