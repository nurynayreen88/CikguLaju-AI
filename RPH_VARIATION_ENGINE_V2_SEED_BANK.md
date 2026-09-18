# RPH Variation Engine v2.1 — Seed Activity Bank

This seed bank operationalises RPH_VARIATION_ENGINE_V2.md using original CikguLaju activity patterns derived from:
- user-supplied Year 1 / phonics lesson-plan examples,
- user-supplied transition-module examples,
- general teacher-resource benchmarking,
while keeping DSKP/RPT/SOW as curriculum source of truth.

## Runtime contract
Each candidate activity is selected only after verified Lesson + exact SK/SP + skill/focus are locked.
Third-party wording must never be copied into runtime output.

## Seed variants

| id | family | skill/focus | difficulty | min | grouping | materials | evidence | notes |
|---|---|---|---|---:|---|---|---|---|
| RPHV2_001 | PRE_WARMUP | vocabulary | core | 5 | pair | word/picture cards | oral recall | quick retrieval and pair compare |
| RPHV2_002 | PHONICS_SOUND_ACTION | phonics/listening | core | 8 | whole_class | audio/phoneme cards | correct sound response | hear sound, respond with agreed action |
| RPHV2_003 | LISTEN_IDENTIFY | listening | core | 8 | individual+pair | audio, picture sheet | identified target item | individual response then pair check |
| RPHV2_004 | PICTURE_MATCH | vocabulary/reading | remedial | 8 | pair | picture+word cards | correct matching | low-reading-load support |
| RPHV2_005 | CHANT_SONG | pronunciation/phonics | core | 6 | whole_class | audio/lyrics prompt | participation+pronunciation | short controlled repetition |
| RPHV2_006 | GUIDED_INPUT | language input | core | 8 | whole_class | board/textbook/visual | guided response | teacher model then pupil echo/response |
| RPHV2_007 | MOVEMENT_TPR | listening/instructions | core | 8 | whole_class | instruction cards | correct action | physical response to target language |
| RPHV2_008 | PAIR_DIALOGUE | speaking | core | 10 | pair | prompt cards | pair performance | structured dialogue using lesson language |
| RPHV2_009 | ROLE_PLAY | speaking | extension | 12 | pair/group | role cards/props | performance checklist | apply target language in simple context |
| RPHV2_010 | PAIR_CHECK | reading/listening | core | 5 | pair | textbook/worksheet | corrected response | compare answers before class check |
| RPHV2_011 | SORT_CLASSIFY | vocabulary/reading | core | 10 | group | cards/category mat | classified set | category reasoning with lesson vocabulary |
| RPHV2_012 | PICTURE_DICTIONARY | vocabulary/reading | core | 12 | pair | picture dictionary/visual bank | listed/categorised words | support lexical retrieval |
| RPHV2_013 | GUIDED_READING | reading | core | 12 | pair/whole_class | short verified text | located information | model strategy then guided response |
| RPHV2_014 | GUIDED_WRITING | writing | core | 12 | individual | writing frame/word bank | short written product | scaffolded production |
| RPHV2_015 | TEXTBOOK_TASK | any textbook-linked skill | core | 10 | individual+pair | textbook | completed task | page-linked task then pair compare |
| RPHV2_016 | PROJECT_POSTER | writing+speaking | extension | 20 | pair/group | poster paper, visuals, glue | product+oral description | application task |
| RPHV2_017 | INFORMATION_GAP | speaking/listening | extension | 12 | pair | A/B cards | exchanged information | meaningful two-way communication |
| RPHV2_018 | MINI_PRESENTATION | speaking | extension | 10 | individual/pair | prompt/product | short presentation | production and confidence |
| RPHV2_019 | WORKSHEET | reading/writing | core | 10 | individual | worksheet | completed items | evidence-producing independent practice |
| RPHV2_020 | PBD_CHECK | any | core | 5 | individual | checklist/exit card | observable evidence | attach to task, not generic assessment |
| RPHV2_021 | POST_RECAP | any | core | 5 | whole_class | board/cards | exit response | recap target learning |
| RPHV2_022 | POST_GAME | vocabulary/phonics | core | 5 | pair/group | cards | correct responses | short retrieval game |
| RPHV2_023 | REMEDIAL_FOUNDATION | foundational literacy | remedial | 10 | small_group | large-print cards, pictures | supported recognition | reduce text load and task steps |
| RPHV2_024 | ENRICHMENT_EXTENSION | any | extension | 10 | pair/individual | challenge card | extended response | deeper application without changing SK/SP |
| RPHV2_025 | GAME | vocabulary/speaking | core | 10 | group | game cards | correct target-language use | structured game with learning evidence |
| RPHV2_026 | GROUP_TASK | integrated | core | 15 | group | task sheet/materials | group product | roles + collaborative output |
| RPHV2_027 | LISTEN_MIME | listening | remedial/core | 8 | whole_class | audio/instructions | correct mime | comprehension before production |
| RPHV2_028 | WORD_MATCH | reading/vocabulary | remedial/core | 8 | pair | word/phrase cards | correct pairings | supports decoding and meaning |
| RPHV2_029 | POST_REFLECTION | metacognition | core | 4 | individual | simple reflection prompt | pupil self-report | age-appropriate reflection |
| RPHV2_030 | PRODUCTION_TASK | integrated application | core/extension | 15 | pair/individual | lesson-specific prompt | final product/performance | final application stage |

## Route recipes
Use recipes as weighted templates, not fixed text.

### PHONICS_A
PRE_WARMUP → PHONICS_SOUND_ACTION → LISTEN_IDENTIFY → PICTURE_MATCH → CHANT_SONG → PBD_CHECK → POST_GAME

### LISTENING_A
PRE_WARMUP → GUIDED_INPUT → LISTEN_MIME → LISTEN_IDENTIFY → PAIR_CHECK → PBD_CHECK → POST_RECAP

### SPEAKING_A
PRE_WARMUP → GUIDED_INPUT → PAIR_DIALOGUE → ROLE_PLAY → PBD_CHECK → POST_REFLECTION

### READING_A
PRE_WARMUP → GUIDED_READING → TEXTBOOK_TASK → PAIR_CHECK → SORT_CLASSIFY → PBD_CHECK → POST_RECAP

### WRITING_A
PRE_WARMUP → GUIDED_INPUT → GUIDED_WRITING → PAIR_CHECK → PRODUCTION_TASK → PBD_CHECK → POST_REFLECTION

### LOW_READINESS_A
PRE_WARMUP → REMEDIAL_FOUNDATION → PICTURE_MATCH → PAIR_CHECK → WORKSHEET → PBD_CHECK → POST_GAME

### PROJECT_A
PRE_WARMUP → GUIDED_INPUT → SORT_CLASSIFY → PROJECT_POSTER → MINI_PRESENTATION → PBD_CHECK → POST_REFLECTION

## Two-session progression
For a verified repeated RPT block with same lesson number/SK/SP:
Session 1 uses input/recognition/controlled practice families.
Session 2 must use retrieval/application/production/assessment families.
Do not generate two near-identical routes.

## Selection scoring
Candidate score =
+40 exact skill/focus match
+30 exact level band match
+15 duration fit
+10 class-size fit
+10 BBM availability fit
+10 route novelty
-25 repeated family from previous RPH
-40 skill mismatch
-100 curriculum mismatch

Only candidates with no curriculum mismatch are eligible.

## Future DB schema
Suggested table: rph_activity_variation_v2
- id
- code
- subject
- level_band
- main_skill
- complementary_skill
- focus_type
- activity_family
- difficulty
- estimated_minutes
- class_size_min
- class_size_max
- grouping
- materials_required
- activity_pattern
- assessment_evidence
- suitable_for_multi_session
- source_pattern
- originality_status
- active
- created_at

Suggested route-history table: rph_variation_history_v2
- id
- user_key
- class_key
- rpt_entry_id
- route_signature
- created_at

This document is a seed bank, not a curriculum source.


## PRIMARY YEAR 1 ENGLISH — VERIFIED CONTENT-FIRST SEED RULES

These rules are grounded in the user-supplied Primary Year 1 Scheme of Work and lesson-plan references.

### SOW structure lock
Primary Year 1 lessons include both textbook-based and non-textbook-based lessons.
- From Lesson 6 onward, textbook-based lessons use Superminds 1 as the lesson spine.
- Non-textbook-based lessons recycle/consolidate previously learned language and skills.
- Main and complementary standards may target different skills in the same lesson.
- RPH objectives may be derived from both, but the main skill remains primary.

### Differentiation patterns extracted from the verified SOW
Use as selectable differentiation logic:
- vary task difficulty;
- vary amount/type of support: teacher talk, gestures, visuals, written support;
- vary expected outcome;
- vary time allowance;
- vary grouping/roles;
- use closed vs open questions appropriately;
- vary feedback according to pupil readiness.
For low-literacy pupils, use supplementary foundational literacy support where the SOW indicates this is appropriate.

### Content-specific route example: Friends — colours / classroom instructions
When a verified Lesson Content Pack contains the colour language and classroom-instruction focus:
- PRE: activate colour words through a quick recognition/retrieval task.
- INPUT: teacher models short supported classroom instructions linked to colours.
- GUIDED RESPONSE: pupils point to real classroom objects matching the instructed colour.
- CONTROLLED PRACTICE: pupils repeat in small groups.
- APPLICATION: game-like instruction-following task using the same colour vocabulary.
- WRITING LINK: pupils write/copy the verified target colour words when the complementary writing standard applies.
- POST: extend to two-item instructions or memory/retrieval using the same verified language.
Do not reuse these colour-specific steps for unrelated lessons.

### Content-specific route example: Friends — colour-word reading / phonics
When the Lesson Content Pack is verified as colour-word recognition / sound-letter work:
- PRE: retrieve colour vocabulary already taught.
- INPUT: identify letter shapes and target initial sounds from verified colour words.
- GUIDED PRACTICE: model segmentation/blending or letter-to-sound connection as required by the verified standard.
- PAIR/GROUP PRACTICE: pupils assemble or match sound/letter units to form the verified colour words.
- WRITING: pupils record the target words with visual colour support.
- PBD: observe recognition, sound production, blending/word formation, or legible written response according to the locked SK/SP.
This pattern must only be selected when the verified lesson content supports it.

### Content-specific route example: At School — project/application
When the Lesson Content Pack contains classroom/school vocabulary and a project-style task:
- use the textbook/source task as the application spine;
- scaffold pupils to identify/categorise the verified vocabulary first;
- move into pair/group product creation;
- require oral description/presentation using the same verified language;
- assess the product and/or oral response against the linked skill.
Generated CikguLaju follow-up should use a different response format from the source task.

### Pre/Post activity library grounded in Year 1 SOW
Eligible families include:
- remember-and-share;
- missing-item recall;
- phonics odd-one-out / same-sound discrimination;
- pass-the-card vocabulary review;
- spot-the-difference from a known text;
- picture/text connection;
- guess-the-word;
- error correction from pupil work;
- remember-and-say;
- whisper-and-write;
- listen-and-point;
- word ladder;
- memory test using a verified picture;
- personal connection to target vocabulary;
- short pupil reflection on what they remember.

These are route patterns only. Runtime wording and lesson content must be original and tied to the Lesson Content Pack.

### Selection guard
The engine must not choose an attractive activity merely because it is age-appropriate.
It must first pass:
1. exact Lesson Content Pack relevance,
2. main/complementary skill compatibility,
3. exact SK/SP compatibility,
4. textbook/non-textbook lesson type compatibility,
5. class/time/readiness fit.


## PRIMARY YEAR 1 ENGLISH — LESSON CONTENT PACK EXEMPLARS (VERIFIED SOW)

These exemplars show how the engine should convert verified SOW content into lesson-specific RPH logic.

### Lesson 6 — Friends — Listening
Verified SOW:
- Main skill: Listening
- Complementary skill: Speaking
- Language focus: greetings / asking name
- Textbook reference: Superminds 1 p.4
- SOW directs teacher to Teacher's Book for detailed pre/delivery/post lesson.

Engine behaviour:
- Treat p.4 as required source spine once the mapped textbook content is available.
- Objective and success criteria must target listening for specific information + giving basic personal information.
- Do not invent the exact textbook dialogue until p.4 content has been extracted/verified.
- Allowed original extension formats: pair name-exchange, information chain, mini role-play, oral exit response.

### Lesson 7 — Friends — Writing
Verified SOW:
- Main skill: Writing
- Complementary skill: Speaking
- Language focus: numbers 1–10; age question/response
- Textbook reference: Superminds 1 p.5

Engine behaviour:
- Use p.5 content as source spine.
- Writing task must remain primary; speaking can scaffold or reinforce.
- Original alternate-format practice may include number/age card matching, interview-and-record, reorder-and-write, mini whiteboard age response.
- Do not switch to unrelated vocabulary.

### Lesson 8 — Friends — Reading
Verified SOW:
- Main skill: Reading
- Complementary skill: Writing
- Language focus: names of letters of the alphabet
- Textbook reference: Superminds 1 p.6

Engine behaviour:
- Build around letter recognition from the verified textbook content.
- Writing activity supports letter/word formation only where linked by SP.
- Suitable variation families: letter hunt, visual discrimination, letter sorting, read-and-match, short copying/formation task.

### Lesson 9 — Friends — Speaking
Verified SOW:
- Main skill: Speaking
- Complementary skill: Reading
- Language focus: colours; describing an object by colour
- Textbook reference: Superminds 1 p.7

Engine behaviour:
- Speaking production must dominate the RPH.
- Reading/phonics supports production, not replace it.
- Suitable original formats after textbook task: object-description cards, colour guessing, pair information gap, mini presentation.

### Lesson 10 — Friends — Language Arts
Verified SOW:
- Main + complementary focus: Language Arts
- Recycled language: alphabet
- SOW suggests a number-song / body-number performance style activity.

Engine behaviour:
- Use creative response/performance route.
- Preserve recycled-language focus.
- Do not force textbook workflow when the SOW provides a non-textbook creative outline.

### Lesson 11 — Friends — Listening, recycled content
Verified SOW:
- Recycles language from Lessons 6–10: name, age, spelling/alphabet.
- Main skill: Listening
- Complementary: Writing
- SOW activity includes class survey, drawing/writing about a partner, class profile, error correction.

Engine behaviour:
- This is a consolidation lesson. The engine should intentionally reference previously learned textbook language rather than invent new lexical content.
- Route may use survey -> pair product -> class display -> error correction.
- Generated worksheet variation should use a different format from any source worksheet while preserving personal-information targets.

### Lesson 12 — Friends — Speaking, recycled content
Verified SOW:
- Recycles language from Lessons 6–10: name and age.
- Main skill: Speaking
- Complementary: Writing
- SOW uses group chain speaking and written follow-up.

Engine behaviour:
- Prioritise repeated oral production in a structured chain/pair/group format.
- Writing captures or extends the same information.
- Alternate route can use role cards, mingle survey, partner introduction, but must retain the same verified language focus.

### Lesson 13 — Friends — Reading, recycled colours/numbers/personal language
Verified SOW excerpt:
- Main skill: Reading
- Complementary: Writing
- Recycles earlier language.
- SOW uses colour retrieval, letter-card recognition, spelling colour words, then a worksheet.

Engine behaviour:
- Use previously taught colour/letter content as the reading spine.
- If generating a CikguLaju worksheet after the SOW worksheet, choose a DIFFERENT format such as sorting, label-and-colour, odd-one-out, letter assembly, or picture prompt.
- Do not produce another near-identical read-and-colour worksheet.

## CONTENT-FIRST GENERATION TEST

Before accepting an RPH, ask:
1. Can the activity sequence be traced to this exact Lesson's verified language/content focus?
2. Does the main skill visibly dominate?
3. Is the complementary skill used in support?
4. For textbook-based lessons, is the mapped page/content used as the spine?
5. For recycled/non-textbook lessons, is prior lesson content intentionally reused?
6. If a source worksheet/activity-book task exists, is the CikguLaju task a genuinely different format?
7. Would this RPH still make sense if the Lesson title were removed? If it could fit almost any Lesson, reject it as too generic.
