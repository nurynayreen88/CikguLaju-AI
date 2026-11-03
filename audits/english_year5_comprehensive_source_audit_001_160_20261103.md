# CikguLaju English Year 5 — Comprehensive SOW / RPH Source Reference Audit

**Audit date:** 2026-11-03. **Branch:** `english-year5-rph-lesson1`. **Scope:** official Year 5 Scheme of Work, current 160 standalone draft files, historical Workbook mapping XLSX, source scanned textbooks and Drive audio filenames. **Status: DRAF — not READY**.

## Verified results

- GitHub file listing: 160/160 numbered RPH files, zero missing numbers.
- Official SOW lessons: 160/160 records, aligned by Lesson number. Earlier code-presence audit found prescribed SK/SP pairs in all 160 drafts; no new claim of educational content approval.
- Historical source mapping XLSX: 160/160 lesson rows; 131 mapped to Workbook, 27 mapped to literature, 2 teacher-choice projects. This workbook's source-level `READY` **does not** indicate these standalone RPHs are READY or active in production.
- SOW references 80 distinct CD tracks; 80 filenames are present in the Drive audio folder. No claim that narration/recording matches listening task: audio content has not been listened to.
- Source scans received: Student Book 126 physical PDF pages; Teacher Book 162; Workbook 110. **Sampled visual verification**: Lesson 101 SB printed p.58 / TB p.72 / WB p.51; Lesson 133 SB p.76 / TB p.91. The printed-page to PDF-page offsets differ by volume. No claim of all-page manual QA.
- CD2-12 appears twice in Drive with identical SHA-256 (`447d6aab706f91a8949218af09edc05765ee7b5446807e0a9d747b0e0a773cf4`), 742,553 bytes each. Keep canonical filename in references; no need to delete either original.
- Source rule clarified in 27 non-textbook Language Arts drafts: no automatic Student Book, Workbook or English Plus CD assignment. Teacher-select Project lessons 88 and 160 remain teacher-defined; do not create mandatory CS/LS.

## Remaining limitations / approval gate

- **43 of 160** previously screened drafts have fewer than 150 words at the time of the deep-text screening: 28, 37, 38, 39, 40, 52, 56, 57, 58, 59, 60, 62, 66, 67, 68, 69, 70, 71, 73, 76, 77, 78, 79, 80, 86, 87, 88, 89, 90, 95, 96, 97, 98, 99, 100, 109, 110, 133, 134, 136, 137, 138, 139. Word count is an imperfect heuristic; pedagogical completeness and assessment quality still need editorial checks.
- Preliminary string-based screening flagged 18 topic labels and 11 page references; most flags arose from alternate topic spellings, curly apostrophes, or page ranges such as `pp.22–23`, not confirmed source errors. Explicit SOW topics were added where useful. Lesson 133's SB p.76 context was added. Do not count these raw string flags as 29 factual mistakes.
- Workbook pages/exercise values below originate from the *historical* mapping workbook. Their `QA_PASS` state is source data, **not independent re-verification** by this audit; only selected scanned pages were viewed directly.
- Full SB/TB/WB activity-by-activity visual checks, audio-content checks, reference links in runtime, DSKP rubric alignment, RPT sync, one-page A4 Word/PDF rendering, teacher approval and full app integration testing remain outstanding. **No RPH should be marked READY or merged to main from this report alone.**

## 160-Lesson source-and-file ledger

| Lesson | SOW focus | Mapping route | Topic | SB printed p. | TB printed p. | SOW CD files | Mapped WB page | WB activity or literature note | Branch file |
|---:|---|---|---|---:|---:|---|---|---|---|
| 1 | Listening 1 | Textbook/LAW | Free time | 4 | 18 | 1-02, 1-03 | 4 | Starter Vocabulary — Free time, Ex1-5 | `lesson_001.md` |
| 2 | Speaking 1 | Textbook/LAW | Free time | 4 | 18 | 1-04 | 5 | Starter Language Focus — be affirmative/negative; subject pronouns/possessive adjectives, Ex1-6 | `lesson_002.md` |
| 3 | Reading 1 | Textbook/LAW | Free time | - | 19 | 1-05 | 5 | Starter Language Focus — subject pronouns and possessive adjectives, Ex5-6 | `lesson_003.md` |
| 4 | Writing 1 | Textbook/LAW | Free time | 6 | 20 | - | 6 | Starter Vocabulary — Prepositions and everyday objects, Ex1-4 | `lesson_004.md` |
| 5 | Language Arts 1 | Language Arts | This Tooth | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_005.md` |
| 6 | Listening 2 | Textbook/LAW | Free time | 7 | 21 | 1-08 | 7 | Starter Language Focus — Possessive 's; be questions, Ex1-5 | `lesson_006.md` |
| 7 | Speaking 2 | Textbook/LAW | Free time | 7 | 21 | - | 7 | Starter Language Focus — be questions, Ex3-5 | `lesson_007.md` |
| 8 | Reading 2 | Textbook/LAW | Free time | 8 | 22 | 1-09 | 8 | Starter Vocabulary — Basic adjectives, Ex1-4 | `lesson_008.md` |
| 9 | Writing 2 | Textbook/LAW | Free time | 8 | 22 | - | 9 | Starter Language Focus — this/that/these/those; have got, Ex1-5 | `lesson_009.md` |
| 10 | Language Arts 2 | Language Arts | This Tooth | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_010.md` |
| 11 | Listening 3 | Textbook/LAW | Free time | 10 | 24 | 1-12 | 10 | Starter Vocabulary — Countries and nationalities, Ex1-4 | `lesson_011.md` |
| 12 | Speaking 3 | Textbook/LAW | Free time | 10 | 25 | - | 10 | Starter Vocabulary — countries/nationalities introduction practice, Ex1-4 | `lesson_012.md` |
| 13 | Reading 3 | Textbook/LAW | Free time | 11 | 25 | - | 11 | Starter Language Focus — Question words Where/What/Who; conjunctions and/or/but, Ex1-5 | `lesson_013.md` |
| 14 | Writing 3 | Textbook/LAW | Free time | 11 | 25 | - | 11 | Starter Language Focus — conjunctions and/or/but, Ex4-5 | `lesson_014.md` |
| 15 | Language Arts 3 | Language Arts | Cats | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_015.md` |
| 16 | Language Awareness 1 | Textbook/LAW | Free Time | 9 | 23 | - | 4-11 | Starter Unit review — verified exercises across Free time, be, possessives, prepositions, adjectives, have got | `lesson_016.md` |
| 17 | Listening 4 | Textbook/LAW | Towns and cities | 12 | 27 | - | 13 | Unit 1 Language Focus — there's/there are + a/an/some/any; Is/Are there; How many, Ex1-5 | `lesson_017.md` |
| 18 | Speaking 4 | Textbook/LAW | Towns and cities | 13 | 27 | - | 13 | Unit 1 Language Focus — there is/are and place questions, Ex1-5 | `lesson_018.md` |
| 19 | Reading 4 | Textbook/LAW | Towns and cities | 14 | 28 | 1-15 | 13 | Unit 1 Language Focus — Is there/Are there/How many, Ex3-5 | `lesson_019.md` |
| 20 | Writing 4 | Textbook/LAW | Towns and cities | 15 | 29 | - | 13,17 | Unit 1 place questions Ex3-5 + Writing description of town/city Ex1-4 | `lesson_020.md` |
| 21 | Language Arts 4 | Language Arts | Cats | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_021.md` |
| 22 | Consolidation 1 | Textbook/LAW | Towns and cities | 15 | 15 | - | 13,18 | Unit 1 there is/are, some/any + Progress Review place questions, Ex1-5 / Ex1-4 | `lesson_022.md` |
| 23 | Listening 5 | Textbook/LAW | Towns and cities | 16 | 30 | 1-16, 1-17 | 14 | Unit 1 Vocabulary and Listening — Comparing places, Ex1-4 | `lesson_023.md` |
| 24 | Speaking 5 | Textbook/LAW | Towns and cities | 17 | 31 | 1-18 | 15 | Unit 1 Language Focus — Comparative adjectives, Ex1-4 | `lesson_024.md` |
| 25 | Reading 5 | Textbook/LAW | Towns and cities | 19 | 33 | - | 16 | Unit 1 Reading — A description of a place, Ex1-5 | `lesson_025.md` |
| 26 | Writing 5 | Textbook/LAW | Towns and cities | 19 | 33 | - | 17 | Unit 1 Writing — A description of a town or city / position of adjectives, Ex1-4 | `lesson_026.md` |
| 27 | Language Arts 5 | Language Arts | Serenade | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_027.md` |
| 28 | Consolidation 2 | Textbook/LAW | Towns and cities | 20 | 34 | - | 18-19 | Unit 1 Progress Review — Places, questions, comparing places, comparative adjectives, speaking and writing, Ex | `lesson_028.md` |
| 29 | Listening 6 | Textbook/LAW | Options: Extra Listening and Speaking | 92 | 106 | 3-02, 3-03 | 18-19 | Unit 1 Progress Review — Listening comparing places + Speaking asking/saying where places are, Ex4, Ex6 | `lesson_029.md` |
| 30 | Speaking 6 | Textbook/LAW | Options: Extra Listening and Speaking | 92 | 106 | 3-04 | 19 | Unit 1 Speaking — Asking and saying where places are, Ex6 | `lesson_030.md` |
| 31 | Reading 6 | Textbook/LAW | Towns and cities | 106 | 120 | 3-27 | 16,18 | Unit 1 Reading — description of a place + Progress Review reading, Ex1-5 / Ex2 | `lesson_031.md` |
| 32 | Writing 6 | Textbook/LAW | Towns and cities | 106 | 120 | - | 17,19 | Unit 1 Writing — description of a town/city, Ex1-4; Progress Review Writing Ex7 | `lesson_032.md` |
| 33 | Language Arts 6 | Language Arts | Serenade | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_033.md` |
| 34 | Language Awareness 2 | Textbook/LAW | Towns and cities | 20 | 35 | - | 18-19 | Unit 1 Progress Review — complete Unit 1 review, Ex1-7 | `lesson_034.md` |
| 35 | Listening 7 | Textbook/LAW | Days | 22 | 36 | 1-21, 1-22 | 21 | Unit 2 Language Focus — Adverbs of frequency / Present simple affirmative-negative, Ex1-5 | `lesson_035.md` |
| 36 | Speaking 7 | Textbook/LAW | Days | 22 | 36 | - | 20 | Unit 2 Vocabulary — Daily routines, Ex1-4 | `lesson_036.md` |
| 37 | Reading 7 | Textbook/LAW | Days | 22 | 37 | - | 24 | Unit 2 Reading — A busy day, Ex1-5 | `lesson_037.md` |
| 38 | Writing 7 | Textbook/LAW | Days | 23 | 37 | - | 25 | Unit 2 Writing — A special day / also, Ex1-4 | `lesson_038.md` |
| 39 | Language Arts 7 | Language Arts | Watching a Bumble Bee | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_039.md` |
| 40 | Consolidation 3 | Textbook/LAW | Days | 93 | 107 | 3-05, 3-06, 3-07 | 26-27 | Unit 2 Progress Review — Daily routines / review practice, Ex1-8 | `lesson_040.md` |
| 41 | Listening 8 | Textbook/LAW | Days | 24 | 38 | 1-23 | 21 | Unit 2 Language Focus — Present simple affirmative-negative, Ex2-5 | `lesson_041.md` |
| 42 | Speaking 8 | Textbook/LAW | Days | 24 | 38 | 1-24 | 20-21 | Unit 2 Daily routines + present simple practice, Ex1-5 | `lesson_042.md` |
| 43 | Reading 8 | Textbook/LAW | Days | 26 | 40 | 1-25 | 23 | Unit 2 Language Focus — Present simple questions, Ex1-4 | `lesson_043.md` |
| 44 | Writing 8 | Textbook/LAW | Days | 26 | 40 | - | 23 | Unit 2 Language Focus — Present simple questions, Ex1-4 | `lesson_044.md` |
| 45 | Language Arts 8 | Language Arts | Watching a Bumble bee | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_045.md` |
| 46 | Consolidation 4 | Textbook/LAW | Days | 27 | 41 | - | 26-27 | Unit 2 Progress Review — present simple questions/time-related unit review, Ex1-8 | `lesson_046.md` |
| 47 | Listening 9 | Textbook/LAW | Days | 28 | 42 | 1-26 | 22,27 | Unit 2 Special days listening Ex3-4 + Progress Review speaking/plans Ex6 | `lesson_047.md` |
| 48 | Speaking 9 | Textbook/LAW | Days | 28 | 42 | - | 27 | Unit 2 Progress Review — Speaking: Making plans and suggestions, Ex6 | `lesson_048.md` |
| 49 | Reading 9 | Textbook/LAW | Days | 29 | 43 | - | 24-25 | Unit 2 Reading/Writing — A busy day + A special day, Ex1-5 / Ex1-4 | `lesson_049.md` |
| 50 | Writing 9 | Textbook/LAW | Days | 29 | 43 | - | 25,27 | Unit 2 Writing — also, Ex1-4; Progress Review Writing Ex7-8 | `lesson_050.md` |
| 51 | Language Arts 9 | Language Arts | And Something Weird Happened | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_051.md` |
| 52 | Language Awareness 3 | Textbook/LAW | Days | 30 | 44 | - | 26-27 | Unit 2 Progress Review — complete Unit 2 review, Ex1-8 | `lesson_052.md` |
| 53 | Listening 10 | Textbook/LAW | Wild Life | 32 | 46 | 1-28, 1-29, 1-30 | 28 | Unit 3 Vocabulary — Animals, Ex1-4 | `lesson_053.md` |
| 54 | Speaking 10 | Textbook/LAW | Wild Life | 33 | 47 | - | 28 | Unit 3 Vocabulary — Animals, Ex2-4 descriptive animal practice | `lesson_054.md` |
| 55 | Reading 10 | Textbook/LAW | Wild Life | 34 | 48 | - | 29 | Unit 3 Language Focus — Superlative adjectives, Ex1-4 | `lesson_055.md` |
| 56 | Writing 10 | Textbook/LAW | Wild Life | 35 | 49 | - | 29 | Unit 3 Language Focus — comparative/superlative-related adjective practice, Ex1-4 | `lesson_056.md` |
| 57 | Language Arts 10 | Language Arts | And Something Weird Happened | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_057.md` |
| 58 | Consolidation 5 | Textbook/LAW | Wild Life | 94 | 108 | 3-08, 3-09 | 34-35 | Unit 3 Progress Review — Animals / Speaking-Writing review, Ex1-8 | `lesson_058.md` |
| 59 | Listening 11 | Textbook/LAW | Wild Life | 36 | 50 | 1-33, 1-34 | 31 | Unit 3 Language Focus — can/can't for ability, Ex1-5 | `lesson_059.md` |
| 60 | Speaking 11 | Textbook/LAW | Wild Life | 36 | 50 | - | 30 | Unit 3 Vocabulary and Listening — Amazing animals, Ex1-5 | `lesson_060.md` |
| 61 | Reading 11 | Textbook/LAW | Wild Life | 39 | 53 | - | 33 | Unit 3 Writing — Giving examples (for example/such as/like), Ex1-4 | `lesson_061.md` |
| 62 | Writing 11 | Textbook/LAW | Wild Life | 39 | 53 | - | 33 | Unit 3 Writing — Animals in danger, Ex1-4 | `lesson_062.md` |
| 63 | Language Arts 11 | Language Arts | And Something Weird Happened | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_063.md` |
| 64 | Consolidation 6 | Textbook/LAW | Wild Life | 38 | 52 | 1-36 | 35 | Unit 3 Progress Review — Speaking: Asking for permission, Ex7 | `lesson_064.md` |
| 65 | Listening 12 | Textbook/LAW | Wild Life | 40 | 54 | 1-37 | 29,34 | Unit 3 superlatives + Progress Review superlative adjectives, Ex1-4 / Ex3 | `lesson_065.md` |
| 66 | Speaking 12 | Textbook/LAW | Wild Life | 40 | 54 | - | 30-31 | Unit 3 Amazing animals / can for ability practice, Ex1-5 | `lesson_066.md` |
| 67 | Reading 12 | Textbook/LAW | Wild Life | 117 | 131 | 3-34 | 31,35 | Unit 3 can/can't for ability, Ex1-5; Progress Review Ex5-6 | `lesson_067.md` |
| 68 | Writing 12 | Textbook/LAW | Wild Life | 117 | 131 | 3-34 | 31 | Unit 3 Language Focus — questions with can / How...?, Ex3-5 | `lesson_068.md` |
| 69 | Language Arts 12 | Language Arts | And Something Weird Happened | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_069.md` |
| 70 | Language Awareness 4 | Textbook/LAW | Wild Life | 41 | 55 | - | 34-35 | Unit 3 Progress Review — complete Unit 3 review, Ex1-8 | `lesson_070.md` |
| 71 | Listening 13 | Textbook/LAW | Learning World | 42 | 56 | 1-38 | 36 | Unit 4 Vocabulary — School subjects, Ex1-4 | `lesson_071.md` |
| 72 | Speaking 13 | Textbook/LAW | Learning World | 43 | 57 | 1-39 | 36 | Unit 4 Vocabulary — school subjects/preferences, Ex2-4 | `lesson_072.md` |
| 73 | Reading 13 | Textbook/LAW | Learning World | 44 | 58 | 1-40 | 40 | Unit 4 Reading — An exciting school, Ex1-5 | `lesson_073.md` |
| 74 | Writing 13 | Textbook/LAW | Learning World | 45 | 59 | 1-41 | 37 | Unit 4 Language Focus — Present continuous affirmative/negative, Ex1-4 | `lesson_074.md` |
| 75 | Language Arts 13 | Language Arts | And Something Weird Happened | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_075.md` |
| 76 | Consolidation 7 | Textbook/LAW | Learning World | 45 | 59 | - | 37,42-43 | Unit 4 present continuous + Progress Review, Ex1-4 / Ex1-8 | `lesson_076.md` |
| 77 | Listening 14 | Textbook/LAW | Learning World | 46 | 60 | 1-42, 1-43 | 38 | Unit 4 Vocabulary and Listening — Studying a language, Ex1-5 | `lesson_077.md` |
| 78 | Speaking 14 | Textbook/LAW | Learning World | 46 | 60 | - | 38,43 | Unit 4 study-language verbs + present simple/continuous review, Ex1-5 / Ex6 | `lesson_078.md` |
| 79 | Reading 14 | Textbook/LAW | Learning World | 47 | 61 | - | 39 | Unit 4 Language Focus — Present continuous questions; present continuous vs present simple, Ex1-4 | `lesson_079.md` |
| 80 | Writing 14 | Textbook/LAW | Learning World | 47 | 61 | - | 39,41 | Unit 4 present continuous/simple + Writing email, Ex3-4 / Ex1-4 | `lesson_080.md` |
| 81 | Language Arts 14 | Language Arts | Miss Antrobus | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_081.md` |
| 82 | Consolidation 8 | Textbook/LAW | Learning World | 50 | 64 | - | 42-43 | Unit 4 Progress Review — complete unit review, Ex1-8 | `lesson_082.md` |
| 83 | Listening 15 | Textbook/LAW | Learning World | 48 | 62 | 1-44, 1-45 | 38,42 | Unit 4 Vocabulary and Listening — language study/listening practice, Ex1-5 / Review Ex4 | `lesson_083.md` |
| 84 | Speaking 15 | Textbook/LAW | Learning World | 48 | 62 | - | 43 | Unit 4 Progress Review — Speaking: Asking for help when studying, Ex7 | `lesson_084.md` |
| 85 | Reading 15 | Textbook/LAW | Learning World | 49 | 63 | - | 40,43 | Unit 4 Reading school types + review writing vocabulary, Ex1-5 / Ex8 | `lesson_085.md` |
| 86 | Writing 15 | Textbook/LAW | Learning World | 49 | 63 | - | 41,43 | Unit 4 Writing — so / email about school, Ex1-4 / Review Ex8 | `lesson_086.md` |
| 87 | Language Arts 15 | Language Arts | Miss Antrobus | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_087.md` |
| 88 | Project 1 | Project | Teacher to select | - | - | - | - | Teacher-select project; no direct Workbook page verified | `lesson_088.md` |
| 89 | Listening 16 | Textbook/LAW | Food and health | 52 | 66 | 2-02, 2-03 | 44 | Unit 5 Vocabulary — Food, Ex1-4 | `lesson_089.md` |
| 90 | Speaking 16 | Textbook/LAW | Food and health | 52 | 67 | 2-04 | 44,51 | Unit 5 food preferences + review speaking/order language, Ex1-4 / Ex6 | `lesson_090.md` |
| 91 | Reading 16 | Textbook/LAW | Food and health | 54 | 68 | 2-05 | 46,48 | Unit 5 Health adjectives Ex1-5 + Reading A cooking competition Ex1-5 | `lesson_091.md` |
| 92 | Writing 16 | Textbook/LAW | Food and health | 54 | 68 | - | 45 | Unit 5 Language Focus — countable/uncountable + some/any/much/many/a lot of, Ex1-5 | `lesson_092.md` |
| 93 | Language Arts 16 | Language Arts | The Meal | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_093.md` |
| 94 | Consolidation 9 | Textbook/LAW | Food and health | 55 | 69 | - | 45,50 | Unit 5 quantifiers + Progress Review, Ex1-5 / Ex3 | `lesson_094.md` |
| 95 | Listening 17 | Textbook/LAW | Food and health | 96 | 110 | 3-12, 3-13 | 51 | Unit 5 Speaking In a cafe / prices-ordering dialogue, Ex6 | `lesson_095.md` |
| 96 | Speaking 17 | Textbook/LAW | Food and health | 96 | 110 | 3-13, 3-14 | 51 | Unit 5 Speaking — In a cafe, Ex6 | `lesson_096.md` |
| 97 | Reading 17 | Textbook/LAW | Food and health | 56 | 70 | 2-06 | 46-47 | Unit 5 Health adjectives + Imperatives, Ex1-5 / Ex4 | `lesson_097.md` |
| 98 | Writing 17 | Textbook/LAW | Food and health | 56 | 71 | - | 47 | Unit 5 Language Focus — Verb + -ing, Ex1-3 | `lesson_098.md` |
| 99 | Language Arts 17 | Language Arts | The Meal | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_099.md` |
| 100 | Consolidation 10 | Textbook/LAW | Food and health | 57 | 71 | - | 47,50-51 | Unit 5 Verb + -ing / Imperatives + Progress Review, Ex1-4 / Ex1-7 | `lesson_100.md` |
| 101 | Listening 18 | Textbook/LAW | Food and health | 58 | 72 | 2-08, 2-09 | 51 | Unit 5 Speaking — In a cafe / Would you like...? Anything else?, Ex6 | `lesson_101.md` |
| 102 | Speaking 18 | Textbook/LAW | Food and health | 58 | 72 | - | 51 | Unit 5 Speaking — ordering food and drink, Ex6 | `lesson_102.md` |
| 103 | Reading 18 | Textbook/LAW | Food and health | 59 | 73 | - | 49,51 | Unit 5 Writing A food blog — sequencing words, Ex1-4; review writing Ex7 | `lesson_103.md` |
| 104 | Writing 18 | Textbook/LAW | Food and health | 59 | 73 | - | 49,51 | Unit 5 Writing — sequencing First/After that/Next/Finally, Ex1-4 / Ex7 | `lesson_104.md` |
| 105 | Language Arts 18 | Language Arts | Seaside | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_105.md` |
| 106 | Language Awareness 5 | Textbook/LAW | Food and health | 60 | 75 | - | 50-51 | Unit 5 Progress Review — complete unit review, Ex1-7 | `lesson_106.md` |
| 107 | Listening 19 | Textbook/LAW | Sport | 62 | 76 | 2-12 | 52 | Unit 6 Vocabulary — Sports, Ex1-4 | `lesson_107.md` |
| 108 | Speaking 19 | Textbook/LAW | Sport | 63 | 77 | 2-13 | 52 | Unit 6 Vocabulary — sports/team/club and be into, Ex1-4 | `lesson_108.md` |
| 109 | Reading 19 | Textbook/LAW | Sport | 64 | 78 | 2-14 | 56 | Unit 6 Reading — A Paralympic sport / sports word forms, Ex1-5 | `lesson_109.md` |
| 110 | Writing 19 | Textbook/LAW | Sport | 64 | 79 | - | 53 | Unit 6 Language Focus — there was/there were; was/were, Ex1-4 | `lesson_110.md` |
| 111 | Language Arts 19 | Language Arts | Seaside | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_111.md` |
| 112 | Consolidation 11 | Textbook/LAW | Sport | 65 | 79 | - | 53,58 | Unit 6 there was/were + Progress Review, Ex1-4 / Ex1-4 | `lesson_112.md` |
| 113 | Listening 20 | Textbook/LAW | Sport | 66 | 80 | 2-15, 2-16 | 54-55 | Unit 6 regular/irregular past simple + past affirmative, Ex1-5 / Ex1-4 | `lesson_113.md` |
| 114 | Speaking 20 | Textbook/LAW | Sport | 66 | 80 | - | 54,59 | Unit 6 past simple practice + Speaking Last weekend, Ex1-5 / Ex6 | `lesson_114.md` |
| 115 | Reading 20 | Textbook/LAW | Sport | 67 | 81 | 2-17 | 54,56 | Unit 6 past simple in context + Reading Paralympic sport, Ex1-5 | `lesson_115.md` |
| 116 | Writing 20 | Textbook/LAW | Sport | 67 | 81 | - | 55,59 | Unit 6 Past time expressions Ex3-4 + Writing sports star Ex7 | `lesson_116.md` |
| 117 | Language Arts 20 | Language Arts | The Dark | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_117.md` |
| 118 | Consolidation 12 | Textbook/LAW | Sport | 97 | 97 | 3-15, 3-16 | 58-59 | Unit 6 Progress Review + past-event speaking/writing, Ex1-7 | `lesson_118.md` |
| 119 | Listening 21 | Textbook/LAW | Sport | 68 | 82 | 2-18, 2-19 | 53,59 | Unit 6 was/were + Speaking Last weekend, Ex1-4 / Ex6 | `lesson_119.md` |
| 120 | Speaking 21 | Textbook/LAW | Sport | 68 | 82 | - | 59 | Unit 6 Speaking — Last weekend, Ex6 | `lesson_120.md` |
| 121 | Reading 21 | Textbook/LAW | Sport | 69 | 83 | - | 54,56 | Unit 6 regular/irregular past verbs + Reading, Ex1-5 | `lesson_121.md` |
| 122 | Writing 21 | Textbook/LAW | Sport | 69 | 83 | - | 57,59 | Unit 6 Writing — A sports star, Ex1-4; review writing Ex7 | `lesson_122.md` |
| 123 | Language Arts 21 | Language Arts | The Dark | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_123.md` |
| 124 | Language Awareness | Textbook/LAW | Sport | 70 | 84 | - | 58-59 | Unit 6 complete Progress Review / unit language review, Ex1-7 | `lesson_124.md` |
| 125 | Listening 22 | Textbook/LAW | Growing up | 72 | 86 | 2-21, 2-22 | 60 | Unit 7 Vocabulary — Describing people, Ex1-5 | `lesson_125.md` |
| 126 | Speaking 22 | Textbook/LAW | Growing up | 72 | 87 | - | 60 | Unit 7 Vocabulary — describing people, Ex1-5 | `lesson_126.md` |
| 127 | Reading 22 | Textbook/LAW | Growing up | 73 | 87 | - | 60,64 | Unit 7 describing people + Reading A true story, Ex1-5 / Ex1-5 | `lesson_127.md` |
| 128 | Writing 22 | Textbook/LAW | Growing up | 75 | 89 | - | 61 | Unit 7 Language Focus — object pronouns; past simple affirmative/negative, Ex1-4 | `lesson_128.md` |
| 129 | Language Arts 22 | Language Arts | Gulliver’s Travels | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_129.md` |
| 130 | Consolidation 13 | Textbook/LAW | Growing up | 98 | 112 | 3-17, 3-18 | 60,66 | Unit 7 describing people + Progress Review vocabulary/reading, Ex1-5 / Ex1-4 | `lesson_130.md` |
| 131 | Listening 23 | Textbook/LAW | Growing up | 76 | 90 | 2-25, 2-26 | 63 | Unit 7 Language Focus — Past simple questions, Ex1-4 | `lesson_131.md` |
| 132 | Speaking 23 | Textbook/LAW | Growing up | 76 | 90 | - | 62 | Unit 7 Vocabulary and Listening — Life events / past simple, Ex1-5 | `lesson_132.md` |
| 133 | Reading 23 | Textbook/LAW | Growing up | 76 | 77 | - | 63 | Unit 7 Past simple questions, Ex1-4 | `lesson_133.md` |
| 134 | Writing 23 | Textbook/LAW | Growing up | 77 | 91 | - | 63,65 | Unit 7 past-simple questions + Writing biographical questions and answers, Ex1-4 / Ex1-4 | `lesson_134.md` |
| 135 | Language Arts 23 | Language Arts | Gulliver’s Travels | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_135.md` |
| 136 | Consolidation 14 | Textbook/LAW | Growing up | 80 | 94 | - | 64,66 | Unit 7 Reading A true story + Progress Review, Ex1-5 / Ex1-4 | `lesson_136.md` |
| 137 | Listening 24 | Textbook/LAW | Growing up | 78 | 92 | 2-27 | 63,67 | Unit 7 past-simple questions + Progress Review questions, Ex1-4 / Ex5 | `lesson_137.md` |
| 138 | Speaking 24 | Textbook/LAW | Growing up | 78 | - | - | 67 | Unit 7 Speaking — interview with a famous person, Ex6 | `lesson_138.md` |
| 139 | Reading 24 | Textbook/LAW | Growing up | 119 | 133 | 3-36 | 63-64 | Unit 7 Past simple questions + Reading A true story, Ex1-4 / Ex1-5 | `lesson_139.md` |
| 140 | Writing 24 | Textbook/LAW | Growing up | 119 | 133 | 3-36 | 65,67 | Unit 7 Writing — Biographical questions and answers / punctuation, Ex1-4; Review Writing Ex7 | `lesson_140.md` |
| 141 | Language Arts 24 | Language Arts | Gulliver’s Travels | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_141.md` |
| 142 | Language Awareness 7 | Textbook/LAW | Growing up | 81 | 95 | - | 66-67 | Unit 7 Progress Review — complete unit review, Ex1-7 | `lesson_142.md` |
| 143 | Listening 25 | Textbook/LAW | Going away | 82 | 96 | 2-29, 2-30 | 68 | Unit 8 Vocabulary — Things for a holiday, Ex1-4 | `lesson_143.md` |
| 144 | Speaking 25 | Textbook/LAW | Going away | 83 | 97 | 2-30 | 68-69 | Unit 8 holiday vocabulary + be going to plans, Ex1-4 / Ex1-5 | `lesson_144.md` |
| 145 | Reading 25 | Textbook/LAW | Going away | 84 | 98 | 2-31 | 72 | Unit 8 Reading — An adventure day, Ex1-5 | `lesson_145.md` |
| 146 | Writing 25 | Textbook/LAW | Going away | 84 | 98 | - | 69 | Unit 8 Language Focus — be going to affirmative/negative/questions, Ex1-5 | `lesson_146.md` |
| 147 | Language Arts 25 | Language Arts | Gulliver’s Travels | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_147.md` |
| 148 | Consolidation 15 | Textbook/LAW | Going away | 85 | 99 | 2-32 | 69,74 | Unit 8 be going to + Progress Review, Ex1-5 / Ex1-4 | `lesson_148.md` |
| 149 | Listening 26 | Textbook/LAW | Going away | 86 | 100 | 2-33, 2-34 | 70 | Unit 8 Vocabulary and Listening — Weather conditions, Ex1-5 | `lesson_149.md` |
| 150 | Speaking 26 | Textbook/LAW | Going away | 86 | 100 | 2-34 | 70 | Unit 8 Weather conditions / holiday plans listening, Ex1-5 | `lesson_150.md` |
| 151 | Reading 26 | Textbook/LAW | Going away | 87 | 101 | - | 71 | Unit 8 Language Focus — will and won't, Ex1-4 | `lesson_151.md` |
| 152 | Writing 26 | Textbook/LAW | Going away | 89 | 103 | - | 69,71 | Unit 8 be going to + will/won't, Ex1-5 / Ex1-4 | `lesson_152.md` |
| 153 | Language Arts 26 | Language Arts | Gulliver’s Travels | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_153.md` |
| 154 | Consolidation 16 | Textbook/LAW | Going away | 90 | 104 | 2-37 | 74-75 | Unit 8 Progress Review — be going to / will-won't / speaking-writing, Ex1-7 | `lesson_154.md` |
| 155 | Listening 27 | Textbook/LAW | Going away | 99 | 113 | 3-19 | 70,74 | Unit 8 Weather conditions / forecast, Ex1-5 / Review Ex4 | `lesson_155.md` |
| 156 | Speaking 27 | Textbook/LAW | Going away | 99 | 113 | 3-20 | 75 | Unit 8 Speaking — Offers and promises, Ex6 | `lesson_156.md` |
| 157 | Reading 27 | Textbook/LAW | Going away | 111 | 125 | 3-32 | 72 | Unit 8 Reading — An adventure day + Vocabulary Plus, Ex1-5 | `lesson_157.md` |
| 158 | Writing 27 | Textbook/LAW | Going away | 111 | 125 | - | 73,75 | Unit 8 Writing — An email, Ex1-4; Progress Review Writing Ex7 | `lesson_158.md` |
| 159 | Language Arts 26 | Language Arts | Gulliver’s Travels | - | - | - | - | Language Arts uses literature source, not Workbook unit | `lesson_159.md` |
| 160 | Project 2 | Project | Teacher to select | - | - | - | - | Teacher-select project; no direct Workbook page verified | `lesson_160.md` |

## Traceability

- SOW file: `Primary-Year-5-SoW-SK.pdf` (Google Drive ID `1FHJm1tl7IamOSZWIndUMoytm6SGoexAV`).
- Source mapping: `CikguLaju_English_Primary_Y4_Y6_DB_READY_CORRECTED_20260921.xlsx` (Drive ID `1WC2oMTdv5bKIKtbI4kZ-lX-Zd8dZasVMBeuFnUH8JQg`).
- Source volumes: SB Drive `1VsszUcJ59ip7QGPwXJ4RZjT8-Z_qPapN`; TB Drive `14Vpj-DjCbOERXdx7rGG8zhzNhsnUEPsM`; WB Drive `1cmRSBYK0_DfKyOOFZW5JazYk7AG6wl8E`.
- Source audio folder: Drive `1A-cDnYRn3j-B5NrvTC5fSaWCg-Gq6YyC`.
- Branch `english-year5-rph-lesson1` only. Main, original databases and deployed services remain unchanged.
