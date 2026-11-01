# English Year 4 — manual approval and release gate register (2026-11-01)

**Scope:** 160 standalone lessons on staging/english-year4-standalone-20261030. This register is a review aid, not a certificate that 160 lessons have been individually checked. Never merge, deploy, or update the production DB based on this register alone.

## Mandatory teacher-selected standards / topics

| Lesson | Type | Required teacher decision | Status |
|---|---|---|---|
| 080 | PBL 1 | Topic, Main SP, Complementary SP, criteria | BLOCKED |
| 096 | Language Awareness 5 | Main SP, Complementary SP, criteria | BLOCKED |
| 112 | Language Awareness 6 | Main SP, Complementary SP, criteria | BLOCKED |
| 128 | Language Awareness 7 | Main SP, Complementary SP, criteria | BLOCKED |
| 144 | Language Awareness 8 | Main SP, Complementary SP, criteria | BLOCKED |
| 160 | PBL 2 | Topic, Main SP, Complementary SP, criteria | BLOCKED |

These lessons have optional teacher planning and individual PBD worksheets under resources/. Those do not resolve the standards or approve a topic.

## Audio/source gates

| Lesson | Source currently stated in RPH | Unresolved |
|---|---|---|
| 123 | Phonics 9 CD3 Tracks 30–31 | Verify playback and target sound items |
| 135 | SB p.95 Activity 5 | Verify names and vocabulary against actual printed text |
| 139 | Track 60 | Disc unverified; audio answer including 'basketball' unverified |
| 145 | Vocabulary Track 68 | Disc unverified; playback and exact health words unverified |
| 147 | Activity 1 Track 72 | Disc unverified; playback and exact story facts unverified |
| 150 | CD2 Tracks 73–74 | Verify playback, printed characters and item count |
| 152 | CD2 Tracks 75–76 | Verify playback, printed text and reading details |
| 155 | CD2 Track 78 | Verify playback and spoken safety details |
| 156 | CD2 Track 79 | Verify playback and board-game language |

The table is a targeted set of known gates, not an exhaustive inventory of all 160 audio/source checks.

## Per-lesson approval record (duplicate for each lesson)

Lesson: ___  Unit: ___  Reviewer: ___  Date: ___
- [ ] Source Student's Book / Teaching Guidebook checked against names, words, characters and activity
- [ ] Workbook page and exercise confirmed, or genuinely not prescribed
- [ ] Audio disc, track and playback verified, or not applicable
- [ ] Main SP and Complementary SP matched to verified SOW/DSKP, including teacher-selected decisions
- [ ] PBD provides separate observable evidence for both standards
- [ ] Original teacher-created materials clearly labelled and source-compatible
- [ ] One-page A4 Word render inspected for layout, completeness and text overflow
- [ ] PDF render inspected for fonts, text and layout
- [ ] Reviewer explicitly approved this lesson

Approval outcome: PENDING / REVISE / APPROVED
Evidence / corrected reference: ___
Reviewer signature or recorded decision: ___

## Release rule

Do not label any lesson READY until its own approval record is complete. A clean adapter parser, worksheet presence or zero automated blockers is not release approval. Preserve original files and DB; apply changes through reviewed staging commits only.
