# English Y2–Y6 release checkpoint — 3 November 2026

**Decision: NOT FINAL READY for all 800.** Keep the existing teacher-facing production paths, permissions, quotas and database unchanged until source and delivery gates pass.

## Verified from current sources

- 800/800 standalone lesson files and matching SOW header LS pairs were audited in merged PR #159/#160.
- 800 Word/A4 files produced in the *offline* second pass (PR #164), including Y5 draft teacher-choice preview. This **does not** prove native PDF, Telegram delivery or classroom readiness.
- Five overflow Word exports in Y2 were addressed through merged PR #165; Y5 continues DRAF/disabled.
- English Y4 Lesson 30: Teacher's Book p39 specifies Class CD1 Track 29, conflicting with printed SOW CD2 Track 29. Current lesson references CD1, but playback and user delivery unverified.
- All 33 teacher-choice lessons exist: Y4=10, Y5=9, Y6=14. These are **not** uniform textbook-free lessons: Language Awareness may use SB/TB/WB. Where SOW leaves CS/LS blank, teacher confirmation is mandatory.
- **Issue resolved in this PR:** Y4 ten teacher-choice lessons previously said `READY — provisional` while simultaneously saying teacher approval pending. Their QA labels now say DRAF without changing teaching content.

## Reproducible release blocker: published Year 6 RPT PDF is stale

Compared on 3 November 2026:
- Google Sheet `MASTER ENGLISH 800 LESSON 2027`, spreadsheet `1aDPXUWhu8HoCamk4Kj0M0Ywwe720SkyEEQDrw41MOtQ`, rows 656 and 662 reference *The Sandwich* by Tony Bradman, Anthology pp28–29.
- Existing published PDF `RPT_ENGLISH_TAHUN_6_2027_UNTUK_GURU.pdf`, Drive file `1mbbfOZyXcxXt3ZknaCHJxGu6kkaxag8e`, has correct Lesson 15/21 topic **but still displays** `Anthology of Poems p.27 — Messing About (SOW)` under their reference/BBM.
- Lessons 25, 26, 31 and 37 in the same PDF also still use generic/unverified resource references. The master Sheet has more specific corrections, as shown in PR #159.
- **Required action:** regenerate the five-page-set/year-six PDF from current verified master and preserve original as backup; check extracted text for L15/L21 exact reference, compare all 160 lesson numbers/LS, confirm landscape layout and page breaks, then replace the file served by Telegram **only after** staging checks. Do not relabel the old PDF FINAL VERIFIED.

## Remaining mandatory gates

1. Source-level audit of all 800 SB/PB/TB/WB activity/exercise locations; verify audio CONTENT by playback rather than file name or metadata alone.
2. Teacher approval for each of the 33 teacher-selected lessons, especially project materials, standards and PBD.
3. Native PDF one-page A4 and live Telegram Word/PDF and resource delivery tests with real paid and trial users, including quota accounting and callback lesson identity.
4. Regenerate stale Year 6 published PDF and check that the Telegram served asset has the new checksum/contents.
5. Mark READY **per Lesson only** on its own evidence; never infer readiness of all 800 from green CI.

This checkpoint makes **no** claim that the PDF has been rebuilt, production has been modified, or the remaining tests were completed.
