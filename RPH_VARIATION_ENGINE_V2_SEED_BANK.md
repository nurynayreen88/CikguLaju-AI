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


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 14–22

### Lesson 14 — Friends — Writing
Verified SOW:
- Main skill: Writing
- Complementary: Reading
- Recycles colours/numbers/personal language from Lessons 6–10
- Uses colour flashcards, pelmanism, poster creation, display/talk, and optional worksheet support.

Engine behaviour:
- Writing remains primary.
- Use colour-word retrieval before written production.
- Project/product task may be used because the SOW itself supports it.
- If generating a worksheet, do not duplicate the SOW-style draw-and-write layout; use an alternate format such as label-and-colour, word assembly, categorise-and-write, or mini caption task.

### Lesson 15 — Friends — Language Arts
Verified SOW:
- Language Arts main focus
- Speaking complementary
- Pupils respond to chant/rap/rhyme/action song and may create an extra verse.

Engine behaviour:
- Creative/performance route only.
- Original CikguLaju extension can vary gesture creation, verse substitution, visual cue sequencing, or group performance.
- Do not turn this into a generic worksheet-heavy lesson.

### Lesson 16 — Friends — Reading
Verified SOW:
- Main skill: Reading
- Complementary: Listening
- Recycles personal language: name/age/questions
- Textbook: Superminds 1 pp.8–9
- Role-play is indicated as a cross-curricular application context.

Engine behaviour:
- Use pp.8–9 as source spine once exact content is verified.
- Reading comprehension/details must remain primary.
- Listening/role-play should support understanding of the same source content.
- Do not invent the exact story/dialogue if the page content is not extracted.

### Lesson 17 — Friends — Writing
Verified SOW:
- Main skill: Writing
- Complementary: Speaking
- Recycles Friends topic
- Textbook: Superminds 1 p.9
- SOW explicitly includes a fallback if Workbook is unavailable: draw/write examples and number practice.

Engine behaviour:
- Mark this Lesson as WORKBOOK_EXPECTED_OR_FALLBACK.
- If verified Workbook mapping is available, use it explicitly.
- If not, use the verified SOW fallback rather than pretending a workbook page is known.
- CikguLaju follow-up must use a different format from whichever source/fallback task is used.

### Lesson 18 — At School — Listening
Verified SOW:
- Main skill: Listening
- Complementary: Speaking
- Language focus: classroom objects
- Textbook: Superminds 1 p.10

Engine behaviour:
- Listening comprehension of classroom-object language is primary.
- Speaking is used for naming/describing after listening.
- Original follow-up may use listen-and-point, object hunt, picture selection, or pair naming, but must remain tied to the verified object set.

### Lesson 19 — At School — Speaking
Verified SOW:
- Main skill: Speaking
- Complementary: Listening
- Language focus: What's this? / It's a... / Is it a...? / Yes/No
- Textbook: Superminds 1 p.11

Engine behaviour:
- Spoken question-answer production is the spine.
- Listening supports comprehension of partner questions.
- Suitable alternate formats: mystery-object bag, pair guessing, object-card information gap, mini speaking carousel.
- Do not replace speaking with a written worksheet as the main task.

### Lesson 20 — At School — Language Arts
Verified SOW:
- Classroom objects
- Recycles chant from p.10
- Pupils make a zigzag book, draw/label 5 classroom objects, and share/name objects.

Engine behaviour:
- Product creation + oral sharing are both required route families.
- CikguLaju variation may change craft/product format, but must preserve imaginative response and classroom-object language.
- Do not generate a second identical zigzag-book task.

### Lesson 21 — At School — Listening
Verified SOW:
- Main skill: Listening prediction
- Complementary: Listening instructions
- Recycles colours/classroom objects
- SOW uses picture dictation and pair picture dictation.

Engine behaviour:
- Prediction must happen before listening.
- Use classroom-object/colour language from prior lessons.
- If generating extra practice, choose a different response mode such as select-the-picture, sequence instructions, or listen-and-build rather than another picture dictation.

### Lesson 22 — At School — Speaking
Verified SOW:
- Main skill: Speaking
- Complementary: Listening
- Recycles greetings, age, numbers
- SOW uses telephone-style pair exchanges with number cards.

Engine behaviour:
- Oral interaction is primary.
- Pair rotation / speaking chain / role card variants are suitable.
- CikguLaju variation should not repeat the exact telephone-card format; use an alternate interaction structure while retaining the same language targets.


## RPH REFERENCE BENCHMARK — USER-SUPPLIED RPH PATTERNS LOCK

The user-supplied Year 1 RPH files have now been rechecked and their usable pedagogical patterns are explicitly locked into the variation bank.

### Patterns verified from supplied RPH examples

**Friends**
- introduce target phrases with teacher/pupil modelling;
- pair practice before whole-class reporting;
- scale from pairs -> small groups -> larger groups -> whole class;
- post-lesson memory/retrieval using pupil names;
- close with target social language such as greetings/goodbyes.

**Colours / classroom instructions**
- introduce/review colour vocabulary;
- teacher gives supported instructions tied to visible classroom objects;
- pupils respond physically;
- transfer control to small groups;
- include a game-like response structure;
- follow with writing of the same verified target words.

**At School**
- flashcard/picture-word correction before new input;
- model target classroom-object language;
- move from recognition to pair/group response;
- use realia/flashcards where useful;
- allow pupils to compare/check with peers before teacher feedback.

**Phonics**
- listen to sound -> perform action;
- identify sound in words;
- discriminate/circle matching pictures;
- sing/chant target sounds;
- follow with pair reading/questions, picture-word matching or another retrieval task;
- later rows review earlier phonemes while introducing the new row.

### Generation consequence
A CikguLaju RPH should no longer default to generic prose such as:
"Teacher introduces the topic. Pupils do an activity. Teacher checks answers."

For a verified lesson, generated teaching steps should show:
1. how target content is activated,
2. how the teacher models it,
3. what pupils physically/speaking/reading/writing do,
4. grouping progression,
5. how the source textbook/workbook task is used,
6. how CikguLaju adds an original alternate-format task,
7. what evidence is observed for PBD,
8. how the lesson closes with retrieval/application.

### Reference-pattern quality gate
Reject generated RPH if:
- activity steps have no observable pupil action;
- grouping is unspecified where interaction is expected;
- source content is not visible in the lesson steps;
- there is no progression from model/input to pupil practice;
- the same generic step sequence is reused regardless of skill;
- phonics lessons do not include actual sound recognition/production behaviour;
- speaking lessons are dominated by writing;
- listening lessons lack a listening-response task;
- reading lessons lack a reading/decoding/comprehension behaviour;
- writing lessons lack a visible written product.


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 31–40

### Lesson 31 — At School — Listening
Verified SOW:
- Recycles school objects.
- Main skill: Listening for main idea.
- Complementary: Listening for specific detail.
- SOW uses a short story, missing-item inference, repeated listening, group response, pair-created story, and spot-the-difference post task.

Engine behaviour:
- Listening must include both gist and detail.
- Use a missing-item / selective-listening route only when the mapped content supports it.
- Pair-created retelling may be used as an application extension, not as a replacement for listening evidence.
- PBD evidence can include identifying omitted/missing object and responding to repeated listening cues.

### Lesson 32 — At School — Speaking
Verified SOW:
- Recycles classroom objects and social phrases.
- Main skill: Speaking.
- Complementary: Speaking strategy for asking help/attention.
- SOW uses pair-created dialogue, speaking frame, modelling, rehearsal, exchange and performance.

Engine behaviour:
- Dialogue preparation must stay oral-first.
- Writing should not replace speaking rehearsal.
- Suitable variation: partner carousel, lost-and-found counter, object-return role-play.
- Include support for asking for vocabulary/pronunciation help.

### Lesson 33 — At School — Reading
Verified SOW:
- Main skill: Reading / blending.
- Complementary: Reading / segmenting.
- Recycles school objects and colour words.
- SOW uses sound-by-sound reveal, word cards, realia matching, sound-card word building and worksheet.

Engine behaviour:
- Reading/phonics behaviours must be explicit: blending, segmenting, decoding.
- If CikguLaju generates a follow-up worksheet, do not reproduce the same beginning/final-sound matching format.
- Alternate formats: sound sorting, word building, picture-to-decoded-word selection, phoneme box task.

### Lesson 34 — At School — Writing
Verified SOW:
- Main skill: Writing fixed social phrases.
- Complementary: Writing capital letters in names.
- Recycles object-return language.
- SOW uses word ordering, model message, label/sticker message and optional oral reply.

Engine behaviour:
- Final product must be a real short written message/label.
- Capitalisation must be visibly assessed.
- CikguLaju alternate task may use message-card completion, reorder-and-write or mini lost-and-found note, but not duplicate the sticker-label task exactly.

### Lesson 35 — At School — Language Arts
Verified SOW:
- Focus: listening/responding to song and classroom-item context.
- SOW suggests revisiting song on Superminds 1 p.12 and using classroom items.

Engine behaviour:
- Use song/choreographed response route.
- If exact p.12 content is not extracted, do not invent lyrics or page details.
- Use only verified classroom-item language and an original response/performance extension.

### Lesson 36 — At School — Listening
Verified SOW:
- Main skill: Listening.
- Complementary: Speaking.
- Language focus: This is (my desk) / There's a bag.
- Textbook: Superminds 1 p.16.

Engine behaviour:
- p.16 becomes the source spine once exact page content is verified.
- Listening for specific detail remains primary.
- Speaking extension may ask pupils to describe their own immediate classroom context using the same structures.

### Lesson 37 — At School — Speaking
Verified SOW:
- Main skill: Speaking.
- Complementary: Writing.
- Language focus includes classroom imperatives and simple fixed questions.
- Textbook: Superminds 1 p.17.

Engine behaviour:
- Speaking interaction remains primary.
- Writing can support with short connected words/proper names only where SP requires it.
- Avoid turning this into an imperative-writing worksheet.

### Lesson 38 — At School — Writing
Verified SOW:
- Main skill: Writing.
- Complementary: Reading.
- Recycles colours; primary/secondary colours.
- Textbook: Superminds 1 p.18.

Engine behaviour:
- Written spelling/colour output must be visible.
- Reading supports understanding of the source content.
- Alternate task: classify-and-write, label colour combinations, short guided caption.

### Lesson 39 — At School — Reading
Verified SOW:
- Main skill: Reading for specific information/detail.
- Complementary: Speaking.
- Recycles primary/secondary colours.
- Textbook: Superminds 1 p.19.

Engine behaviour:
- Reading detail must be the evidence spine.
- Speaking is used to name/describe after reading.
- Suitable variation: information hunt, colour-detail matching, read-and-describe.

### Lesson 40 — At School — Language Arts
Verified SOW:
- Reviews imperative verbs + please.
- Main skill: imaginative response.
- Complementary: Listening to supported instructions.
- SOW uses mime, puppet-led chant, action-on-please, pupil-made puppets and group chant.

Engine behaviour:
- Must include listening-for-cue and imaginative/product response.
- Politeness/please is part of the content focus.
- Original CikguLaju variation may alter puppet/craft/performance format but must preserve imperative + please response.
- Do not reduce this lesson to a worksheet.
