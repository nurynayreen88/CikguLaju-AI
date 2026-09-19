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


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 41–50

### Lesson 41 — At School — Listening
Verified SOW:
- Recycles colours and classroom objects.
- Main skill: Listening for specific detail.
- Complementary: Listening to supported questions.
- SOW uses whisper-chain colour transmission, memory of object colours, question-response and group replay.

Engine behaviour:
- Require active listening-response evidence.
- Use colour/object memory only when the Lesson Content Pack matches.
- Alternate CikguLaju formats: listen-select, colour/object matrix, audio memory grid.
- Avoid reusing the same whisper-chain route in consecutive RPHs.

### Lesson 42 — At School — Speaking
Verified SOW:
- Recycles classroom imperatives + please/thank you.
- Main skill: Speaking.
- Complementary: Listening to supported instructions.
- SOW explicitly connects to instruction patterns similar to textbook p.17.

Engine behaviour:
- Speaking pupils must give the instructions, not only follow them.
- Preserve politeness markers.
- Suitable variation: command-card carousel, pair instruction challenge, sequence-and-say.
- PBD can observe intelligible instruction + appropriate social phrase.

### Lesson 43 — At School — Reading
Verified SOW:
- Main skill: sound out beginning/medial/final sounds.
- Complementary: spelling familiar words.
- Uses colour-word matching, numbered colour key, pupil-created picture/key exchange.

Engine behaviour:
- Reading/decoding and spelling must both be visible.
- CikguLaju follow-up should not merely reproduce number-key colouring.
- Alternate formats: decoded-word hunt, sound-to-colour sort, spell-and-label, phoneme box.

### Lesson 44 — At School — Writing
Verified SOW:
- Main skill: spelling familiar high-frequency words.
- Complementary: reading instructions for detail.
- Uses colour wheel, labelled writing, dice-driven instruction reading, pupil-written new instructions.

Engine behaviour:
- Require a written product.
- Reading serves the writing task.
- Alternate formats: instruction-card creation, classify-and-write colour words, error-correction + rewrite.
- Do not repeat the exact dice game if the source task was already used.

### Lesson 45 — At School — Language Arts
Verified SOW:
- Reviews primary and secondary colours.
- Uses guessing, colour grouping, song response, colour wheel creation and prediction.
- Links Language Arts with imaginative craft response.

Engine behaviour:
- Preserve creative/performance/product character.
- Generated activity may vary song/craft format but must remain tied to colour concepts.
- Do not turn into a generic colouring worksheet.

### Lesson 46 — At School — Listening
Verified SOW:
- Main skill: listening to short basic classroom instructions.
- Complementary: asking for attention/help.
- Textbook: Superminds 1 p.20.
- Focus includes imperatives such as look down, catch, turn around, stretch, cut out, fold, glue.

Engine behaviour:
- p.20 is source spine once exact content is verified.
- Include opportunity for pupils to ask for help/clarification.
- Alternate format: sequence instructions, action stations, listen-and-build/craft.

### Lesson 47 — At School — Writing
Verified SOW:
- Main skill: writing/name or describe classroom objects.
- Complementary: using a picture dictionary.
- Textbook: Superminds 1 p.21.
- SOW explicitly provides a fallback if Workbook is unavailable and lists classroom-object vocabulary.

Engine behaviour:
- Mark as WORKBOOK_EXPECTED_OR_FALLBACK.
- If workbook mapping exists, use it explicitly; otherwise use SOW fallback.
- Generated CikguLaju practice must use a different format from the source/fallback task.
- Picture-dictionary use should be visible in the lesson plan.

### Lesson 48 — Let's Play! — Speaking
Verified SOW:
- Theme: World of Stories.
- Main skill: Speaking.
- Complementary: Listening.
- Vocabulary includes toys/vehicles/games.
- Textbook: Superminds 1 p.22.

Engine behaviour:
- Speaking production with toy vocabulary must dominate.
- Listening supports model/input.
- Alternate formats: toy-shop role-play, mystery-toy guessing, preference carousel, picture prompt speaking.

### Lesson 49 — Let's Play! — Reading
Verified SOW:
- Main skill: Reading for specific information/details.
- Complementary: Speaking for basic personal information.
- Language focus includes pronouns/possessives/favourite.
- Textbook: Superminds 1 p.23.
- SOW gives fallback when stickers are unavailable.

Engine behaviour:
- Reading detail remains primary.
- Speaking extension should recycle the same personal/favourite information.
- Do not copy the sticker-placement task; alternate CikguLaju formats may use information hunt, read-and-match, profile-card completion.

### Lesson 50 — Let's Play! — Language Arts
Verified SOW:
- Main skill: personal response to literary text.
- Complementary: listening to a very short simple narrative.
- Story should relate to Unit 1/textbook content or other familiar learning.
- Interactive/digital story is optional; acting out is a fallback.

Engine behaviour:
- Story listening + personal/illustrative response are mandatory.
- Do not invent unfamiliar lexical load unrelated to the unit.
- If digital story unavailable, use acting/sequence-picture/story-response alternatives.
- Generated follow-up should preserve narrative understanding rather than become an unrelated vocabulary worksheet.


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 51–60

### Lesson 51 — Let's Play! — Listening
Verified SOW:
- Recycles imperatives from Lesson 46.
- Main skill: Listening to short supported classroom instructions.
- Complementary: Speaking / naming-describing.
- SOW uses robot role-play, single and sequenced instructions, group rotation and optional written instruction.

Engine behaviour:
- Listening-response must be physical/observable.
- Begin with single instructions, progress to sequences.
- Speaking extension may transfer control to pupils.
- Alternate CikguLaju format: listen-and-build, action sequence cards, command station.
- Do not make writing the main evidence.

### Lesson 52 — Let's Play! — Speaking
Verified SOW:
- Toy vocabulary + name/age/favourite toy.
- Main skill: Speaking / likes-dislikes.
- Complementary: Speaking to group/audience.
- SOW uses survey grid, mingle/group interview, partner reporting, self-report.

Engine behaviour:
- Oral information-gathering is the lesson spine.
- Require pupils to ask and answer, then report another pupil's information.
- Alternate format: speaking carousel, interview cards, toy-preference graph with oral report.
- Written grid is support only.

### Lesson 53 — Let's Play! — Reading
Verified SOW:
- Recycles toy vocabulary.
- Main/complementary: Reading blending + segmenting.
- SOW uses alphabet review, I-spy, anagrams, pair-created anagrams.

Engine behaviour:
- Explicit decoding behaviour required.
- Use toy vocabulary already verified.
- CikguLaju follow-up must not duplicate anagram format if source task already used.
- Alternate formats: phoneme boxes, sound sorting, word-building cards, decode-and-match.

### Lesson 54 — Let's Play! — Writing
Verified SOW:
- Recycles Lesson 49 language.
- Main skill: Writing / expressing likes-dislikes.
- Complementary: Speaking strategy / asking for help.
- SOW uses partner-information gathering, note checking/editing and digital/paper profile writing.

Engine behaviour:
- Final evidence must be a short written profile/product.
- Include editing/spelling check before final write.
- Encourage help-seeking phrase where appropriate.
- Alternate format: profile card, mini blog card, partner fact file, guided paragraph.

### Lesson 55 — Let's Play! — Language Arts
Verified SOW:
- Personal response to illustrated literary text.
- Listening for specific details.
- Language includes name, age, favourite toy/colour.
- SOW uses prediction about characters, listen/read for details, pair check and sentence writing.

Engine behaviour:
- Prediction -> listen/read -> detail retrieval -> personal response.
- Do not overload with unrelated vocabulary.
- Alternate response: character card, picture-detail match, short partner retell.
- Writing remains supportive, not dominant.

### Lesson 56 — Let's Play! — Speaking
Verified SOW:
- Recycled toy vocabulary + favourite.
- Main skill: Speaking.
- Complementary: Writing.
- Textbook: Superminds 1 p.24.

Engine behaviour:
- p.24 is source spine once exact content is verified.
- Spoken personal information remains primary.
- Writing supports capture/reinforcement.
- Suitable variation: show-and-tell, favourite-toy partner interview, mini speaking circle.

### Lesson 57 — Let's Play! — Listening
Verified SOW:
- Focus: a/an and adjectives long, short, big, small, ugly, beautiful, old, new.
- Main/complementary: Listening.
- Textbook: Superminds 1 p.25.

Engine behaviour:
- Listening for specific adjective/object details is required.
- Do not invent exact page dialogue until extracted.
- Alternate formats: listen-and-select, adjective-object matrix, picture discrimination.

### Lesson 58 — Let's Play! — Writing
Verified SOW:
- Toy vocabulary revision.
- Main skill: Writing/spelling.
- Complementary: Reading word-level games.
- SOW uses toy flashcard retrieval and crossword completion.

Engine behaviour:
- Spelling evidence must be visible.
- If source crossword is used, CikguLaju follow-up must be a different format.
- Alternate formats: label picture, word build, missing-letter grid, category-and-spell, error correction.

### Lesson 59 — Let's Play! — Reading
Verified SOW:
- Recycles colours, numbers, toys.
- Main skill: Reading for main idea.
- Complementary: Listening to short narrative.
- Textbook: Superminds 1 p.26.
- Includes fair-play value.

Engine behaviour:
- Reading main-idea task is the evidence spine.
- Listening supports the same source/narrative context.
- Preserve fair-play context when it naturally occurs in verified material.
- Do not turn into isolated vocabulary drill.

### Lesson 60 — Let's Play! — Language Arts
Verified SOW:
- Favourite colour/toy/number.
- Main skill: Language Arts personal response.
- Complementary: Writing words/phrases.
- Explicitly reviews Superminds 1 p.24 song/pictures.
- Pupils talk about favourites, write/draw poster, display work and create new song verses.

Engine behaviour:
- Use p.24 review as source connection.
- Product + personal response + shared performance are valid route components.
- Differentiate writing support according to literacy level.
- CikguLaju variation may change poster/product format but preserve favourite-things content.


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 61–70

### Lesson 61 — Let's Play! — Listening
Verified SOW:
- Recycles adjectives + toys from Lessons 56–60.
- Main skill: Listening prediction.
- Complementary: Listening for specific details.
- SOW uses flashcards similar to p.25, prediction of likely phrases, number-selection listening game, pupil-led group repetition.

Engine behaviour:
- Prediction must happen before listening.
- Listening evidence should show recognition of adjective + toy combinations.
- Alternate CikguLaju formats: listen-and-grid, descriptor bingo, picture-number selection.
- Avoid repeating identical number-bingo mechanics across nearby lessons.

### Lesson 62 — Let's Play! — Speaking
Verified SOW:
- Recycles toy vocabulary.
- Main skill: Speaking / naming and describing.
- Complementary: asking for help/attention.
- SOW uses a rhythmic toy chant, movement, pattern noticing, pair/group chant creation and performance.

Engine behaviour:
- Oral production + rhythm/performance are required.
- Pupils should manipulate the verified toy vocabulary, not add unrelated items.
- CikguLaju variation may use rap cards, chant sequencing or performance groups.
- Include help-seeking language support when needed.

### Lesson 63 — Let's Play! — Reading
Verified SOW:
- Recycles favourite + toy vocabulary.
- Main skill: Reading using visuals.
- Complementary: Writing / naming-describing objects.
- SOW uses move-and-touch warm-up, toy pictures, sentence strips, picture matching and short labels.

Engine behaviour:
- Visual-to-text comprehension must be explicit.
- Reading must precede the written label.
- Alternate formats: picture-sentence hunt, read-and-place, visual clue matching, short captioning.
- Do not turn it into a pure speaking task.

### Lesson 64 — Let's Play! — Writing
Verified SOW:
- Recycles personal/favourite language from Lesson 54.
- Main skill: Writing with appropriate capital letters.
- Complementary: Reading for specific details.
- SOW uses anonymous personal-information slips, redistribution, reading/guessing writer, oral confirmation and reporting.

Engine behaviour:
- Written personal-information product is mandatory.
- Capitalisation of personal names must be assessed.
- Reading-for-detail should be visible in the guessing stage.
- Alternate format: anonymous profile card, mini fact file, read-and-identify.

### Lesson 65 — Let's Play! — Language Arts
Verified SOW:
- Story about toys.
- Main skill: personal response to literary text.
- Complementary: listening to a very short narrative.
- The same story is reused in Lesson 70.

Engine behaviour:
- Save story/source continuity metadata so Lesson 70 can reuse the same source.
- Prepare pupils before story reading.
- Focus on global understanding, illustrations and enjoyment.
- Do not require word-by-word comprehension.

### Lesson 66 — Let's Play! — Reading
Verified SOW:
- Recycles toy vocabulary + adjectives.
- Main skill: Reading phonics.
- Complementary: Listening phonemes.
- Textbook: Superminds 1 p.27.
- Fair play value appears in SOW.

Engine behaviour:
- p.27 is source spine once exact content is verified.
- Reading must include sound recognition/decoding behaviour.
- Listening reinforces the same phoneme target.
- Do not replace with generic vocabulary review.

### Lesson 67 — Let's Play! — Listening
Verified SOW:
- Recycles toys + adjectives.
- Main skill: Listening for specific details.
- Complementary: Reading for specific details.
- Textbook: Superminds 1 p.28.

Engine behaviour:
- Listening and reading should work on the same mapped source/content.
- Listening remains primary evidence.
- Alternate format: listen-read compare, detail matrix, picture selection with written confirmation.

### Lesson 68 — Let's Play! — Writing
Verified SOW:
- Focus: favourite + toy vocabulary + adjectives.
- Main skill: Writing / expressing likes-dislikes.
- Complementary: Speaking.
- Textbook: Superminds 1 p.29.

Engine behaviour:
- Written favourite statement/product is primary.
- Speaking can be used for pair rehearsal/interview first.
- Alternate formats: preference card, mini survey-to-write, captioned favourite-toy profile.

### Lesson 69 — Let's Play! — Speaking
Verified SOW:
- Focus: shapes / tangram vocabulary.
- Main skill: Speaking / naming-describing.
- Complementary: Reading for specific details.
- Textbook: Superminds 1 p.30.

Engine behaviour:
- Shape vocabulary must be spoken and applied.
- Reading supports task instructions/source details.
- Suitable variation: tangram describe-and-build, mystery-shape guessing, shape hunt, pair instruction task.
- Do not reduce to shape colouring only.

### Lesson 70 — Let's Play! — Language Arts
Verified SOW:
- Explicit continuation of Lesson 65 story.
- Main skill: personal response.
- Complementary: imaginative response/art-craft.
- SOW reviews story, re-reads, extends through vocabulary/character/storyline tasks and creative product, then pupil presentation/reflection.

Engine behaviour:
- Must resolve the SAME story/source used in Lesson 65.
- Add continuity key: linked_previous_lesson = 65.
- Route: recall -> reread -> extend -> create -> present/respond.
- If Lesson 65 source is unavailable, do not invent a new unrelated story silently; mark source continuity unresolved and use a teacher-selected verified substitute only if explicitly mapped.


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 71–80

### Lesson 71 — Let's Play! — Listening
Verified SOW:
- Recycles favourite colours, numbers, toys and adjectives.
- Main skill: Listening for specific information/details.
- Complementary: Speaking / naming-describing.
- SOW uses "Change places if..." and a memory-chain activity.

Engine behaviour:
- Listening response must remain observable.
- Movement-based response is valid but should not become the only evidence.
- Chain recall can be used for application/retrieval.
- Alternate formats: listen-and-move, favourite-item response grid, memory chain with cards.

### Lesson 72 — Let's Play! — Speaking
Verified SOW:
- Recycles favourite/toy language.
- Main skill: Speaking / expressing likes-dislikes.
- Complementary: asking for attention/help.
- SOW uses toy list creation, pupil grid, mingle/interview, reporting and optional true/false partner extension.

Engine behaviour:
- Speaking interaction and repeated questioning are primary.
- Grid only supports oral data collection.
- Help-seeking language should be explicitly supported.
- Alternate formats: speaking carousel, interview bingo, find-someone-who using toy preferences.

### Lesson 73 — Let's Play! — Reading
Verified SOW:
- Recycles shapes and known Year 1 language.
- Main skill: recognise letter shapes.
- Complementary: sound out beginning/medial/final sounds.
- SOW uses word-shape outlines, guessing, pupil-created word shapes and cut-and-stick letter construction.

Engine behaviour:
- Reading must involve letter/word-form recognition.
- Phonics and visual word-shape recognition should both appear.
- Alternate formats: word silhouette match, cut-and-build words, letter-shape sort, decode-and-stick.
- Do not reduce to generic shape vocabulary review.

### Lesson 74 — Let's Play! — Writing
Verified SOW:
- Recycles shapes + familiar objects.
- Main skill: spelling familiar words.
- Complementary: planning/writing words and phrases.
- SOW uses object flashcards grouped by shape, board race, spelling correction and writing object words inside shape categories.

Engine behaviour:
- Written categorisation + correct spelling should be the evidence.
- CikguLaju variation may use category cards, label-and-sort or object-shape mini poster.
- Include correction/editing step before final written product.

### Lesson 75 — Let's Play! — Language Arts
Verified SOW:
- Focus: shape vocabulary.
- Main skill: enjoy/respond to song.
- Complementary: personal response to illustrations/texts.
- SOW uses body shapes, pupil-made shape cards, shape song and favourite-shape sharing.

Engine behaviour:
- Performance/non-verbal response must be visible.
- Writing shape names is supportive, not primary.
- Alternate format: movement chant, shape-response cards, class shape performance.
- Preserve song/creative nature.

### Lesson 76 — Let's Play! — Speaking
Verified SOW:
- Recycles shape vocabulary from Lessons 69, 73 and 74.
- Main skill: Speaking / basic personal information.
- Complementary: asking for help.
- Textbook: Superminds 1 p.31.
- Project parts provide opportunities for help-seeking language.

Engine behaviour:
- p.31 is source spine once exact page content is verified.
- Speaking must remain primary.
- If project work is used, ensure each pupil has an oral contribution.
- Include explicit opportunity to ask for vocabulary/material help.

### Lesson 77 — Let's Play! — Reading
Verified SOW:
- Recycles colours, toys, imperatives.
- Main skill: Reading using visuals/high-frequency patterns.
- Complementary: Listening to supported questions.
- Textbook: Superminds 1 p.32.
- SOW provides a fallback paper-doll-chain task if Workbook is unavailable.

Engine behaviour:
- Mark as WORKBOOK_EXPECTED_OR_FALLBACK.
- If Workbook mapping exists, use it; otherwise use SOW fallback.
- Reading of visual/instructional text must be visible.
- CikguLaju alternate task must not duplicate the source craft format.

### Lesson 78 — Let's Play! — Writing
Verified SOW:
- Recycles Unit 2 vocabulary/grammar.
- Main skill: Writing / spelling.
- Complementary: Writing personal information.
- Textbook: Superminds 1 p.33.
- SOW provides a no-Workbook fallback using toy flashcards + picture dictionary.

Engine behaviour:
- Mark as WORKBOOK_EXPECTED_OR_FALLBACK.
- If workbook absent, use verified toy vocabulary fallback.
- Writing/spelling remains primary evidence.
- Alternate formats: toy picture dictionary extension, label-and-write, categorise-and-spell.

### Lesson 79 — Pet Show — Listening
Verified SOW:
- Theme: World of Knowledge.
- Main skill: Listening.
- Complementary: Speaking.
- Animal vocabulary includes elephant, rat, lizard, frog, spider, duck, dog, cat.
- Textbook: Superminds 1 p.34.

Engine behaviour:
- p.34 becomes source spine once exact content is verified.
- Listening for main idea must precede speaking/naming extension.
- Alternate formats: listen-and-point, animal-picture selection, identify-the-pet.

### Lesson 80 — Pet Show — Language Arts / Unit 2 Review
Verified SOW:
- Complete review of Unit 2 Superminds 1.
- Main skill: imaginative response.
- Complementary: Writing / naming-describing.
- SOW suggests reviewing Unit 2 songs/chants/stories, drawing and writing what pupils learned, and sharing written work.

Engine behaviour:
- Treat this as a consolidation/review lesson, not new content.
- Source pages must come from verified Unit 2 mapping.
- Product can be drawing + short text or alternate review artefact.
- Generated RPH should show retrieval, product creation and sharing/reflection.
- Do not introduce unrelated new vocabulary.


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 81–90

### Lesson 81 — Pet Show — Listening
Verified SOW:
- Recycles animal vocabulary, adjectives and a/an.
- Main skill: Listening for specific information/details.
- Complementary: Speaking / naming-describing.
- SOW uses an adjective + animal grid, secret selections and guessing.

Engine behaviour:
- Listening evidence must capture adjective + animal combinations.
- Speaking may be used as guessing/response support.
- Alternate formats: listen-select grid, adjective-animal bingo, picture-detail match.
- Do not reuse the same secret-grid format in adjacent lessons.

### Lesson 82 — Pet Show — Speaking
Verified SOW:
- Animal vocabulary + favourite questions.
- Main skill: Speaking to find out basic personal information.
- Complementary: Speaking likes/dislikes.
- SOW uses a snapdragon/fortune-teller craft with colour, number and favourite questions.

Engine behaviour:
- Speaking interaction remains the real objective; craft is a vehicle.
- If craft is too difficult, use teacher-prepared material rather than removing oral interaction.
- Alternate CikguLaju formats: question spinner, favourite-card wheel, pair prompt cards.
- Preserve cooperative support.

### Lesson 83 — Pet Show — Reading
Verified SOW:
- Recycles animal vocabulary.
- Main skill: Reading / blending.
- Complementary: Reading word-level games.
- SOW uses gapped spelling review, word snake/sausage, pair-created puzzles.

Engine behaviour:
- Explicit decoding and word recognition required.
- If source word-snake is used, alternate CikguLaju practice should use a different format.
- Alternate formats: phoneme boxes, decode-and-match, letter build, animal-word sort.

### Lesson 84 — Pet Show — Writing
Verified SOW:
- Animal vocabulary + favourite animal.
- Main skill: Writing likes/dislikes.
- Complementary: capital letters in names.
- SOW uses mime recall, spelling review, model sentence and repeated pupil writing.

Engine behaviour:
- Written sentence about a named person's favourite animal is the primary product.
- Capitalisation must be checked.
- Alternate formats: profile card, sentence strip reorder-and-write, favourite-animal mini fact.
- Include peer/whole-class reading only after the written evidence.

### Lesson 85 — Pet Show — Language Arts
Verified SOW:
- Animal vocabulary from Superminds p.34.
- Main skill: imaginative response / art-craft.
- Complementary: Speaking / naming-describing.
- Pupils create word and picture cards, then use them in a pelmanism/matching game.

Engine behaviour:
- p.34 vocabulary set is the verified source.
- Product creation + oral naming should both appear.
- Generated CikguLaju variation may use picture-word dominoes, memory cards, mini matching board, but should not duplicate the exact source game every time.
- Preserve reusable-resource logic where possible.

### Lesson 86 — Pet Show — Listening
Verified SOW:
- Focus: prepositions in/on/under.
- Main skill: Listening for specific details.
- Complementary: Speaking / naming-describing.
- Textbook: Superminds 1 p.35.

Engine behaviour:
- p.35 is source spine once exact content is verified.
- Listening task must require location discrimination.
- Speaking extension may describe animal/object position using the same prepositions.
- Alternate formats: listen-and-place, picture selection, position grid.

### Lesson 87 — Pet Show — Speaking
Verified SOW:
- Focus: plural animal nouns + recycled colours/prepositions.
- Main skill: Speaking / naming-describing.
- Complementary: target-language sound recognition/reproduction.
- Textbook: Superminds 1 p.36.

Engine behaviour:
- Spoken plural animal descriptions must dominate.
- Phonological support should reinforce the same target words.
- Alternate formats: describe-the-scene, count-and-say, pair spot-and-describe.
- Avoid making plural writing the main activity.

### Lesson 88 — Pet Show — Reading
Verified SOW:
- Recycles topic vocabulary and likes/dislikes.
- Main skill: Reading for specific information/details.
- Complementary: Speaking likes/dislikes.
- SOW reuses Lesson 85 pelmanism cards, then uses a yes/no or tick/cross reading table.

Engine behaviour:
- Reading sentences for detail must be the evidence spine.
- Speaking personalisation follows reading.
- If source uses tick/cross table, CikguLaju alternate format should differ: profile matching, information hunt, read-and-sort.
- Reuse of earlier BBM is allowed and encouraged when mapped.

### Lesson 89 — Pet Show — Writing
Verified SOW:
- Recycles animals + prepositions + and.
- Main skill: Writing using and.
- Complementary: planning/writing words and phrases.
- SOW uses object placement, false sentences, oral correction, pupil-created picture, written peer correction and final correct sentence.

Engine behaviour:
- Require written correction + final correct sentence.
- Use and meaningfully to connect two pieces of information.
- Strong route: manipulate/observe -> read false sentence -> correct orally -> write -> peer correct -> final rewrite.
- Alternate format: error-correction cards, picture-to-sentence correction, two-clause caption.

### Lesson 90 — Pet Show — Language Arts
Verified SOW:
- Animal vocabulary review/extension.
- Main + complementary: enjoy/respond to chants/raps/songs.
- SOW suggests listening, miming and joining in with an animal chant/rap.

Engine behaviour:
- Performance, rhythm and non-verbal response are mandatory.
- Recycled animal vocabulary should be prioritised before extension.
- Alternate formats: animal action chant, group rap, call-and-response.
- Do not convert into a worksheet-led lesson.


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 91–100

### Lesson 91 — Pet Show — Listening
Verified SOW:
- Recycles animals + prepositions.
- Main skill: Listening to supported questions.
- Complementary: Listening for specific details.
- SOW uses hidden-spider location guessing with classroom objects/pictures and pair/group replay.

Engine behaviour:
- Listening discrimination of prepositions must be observable.
- Alternate formats: listen-and-place, hidden-object map, location-choice cards.
- Avoid converting to a speaking-only guessing game.

### Lesson 92 — Pet Show — Speaking
Verified SOW:
- Recycles prepositions, plural nouns, classroom objects, colours and imperative Put...
- Main skill: Speaking / naming-describing.
- Complementary: Listening to instructions.
- SOW uses object-placement instructions, group turns and a location grid guessing task.

Engine behaviour:
- Pupils must give oral instructions and describe location.
- Listening supports response to classmates.
- Alternate formats: object-position challenge, pair scene-builder, instruction relay.
- Grid is support, not the core outcome.

### Lesson 93 — Pet Show — Reading
Verified SOW:
- Recycles animal vocabulary.
- Main skill: Reading / blending.
- Complementary: Writing / spelling.
- SOW uses 12 animal words, card recognition, group retrieval and matching-memory game.

Engine behaviour:
- Decoding/reading and spelling should both be visible.
- Reusable word cards are encouraged.
- Alternate CikguLaju formats: decode-and-sort, word build, animal label cards.
- Avoid simply duplicating memory/pelmanism if already used.

### Lesson 94 — Pet Show — Writing
Verified SOW:
- Recycles prepositions + topic vocabulary.
- Main skill: Writing words/phrases.
- Complementary: spelling familiar words.
- SOW uses animal-to-object line puzzle, oral sentence creation, written sentences and pupil-created puzzle exchange.

Engine behaviour:
- Final written sentence must encode both animal and location.
- Strong route: solve -> write -> create -> swap -> solve/write.
- Alternate formats: picture-path sentence, location mini-map, sentence builder.
- Include spelling check.

### Lesson 95 — Pet Show — Language Arts
Verified SOW:
- Focus: prepositions of place.
- Main skill: imaginative response/art-craft.
- Complementary: Listening to classroom instructions.
- SOW uses teacher dictation to Pupil 1, peer redictation to Pupil 2, drawing, colour negotiation, final joint picture and display.

Engine behaviour:
- Listening memory + creative product are both essential.
- Preserve pair negotiation/compromise.
- Alternate format: listen-draw-compare, collaborative scene board, picture reconstruction.
- Do not reduce to passive colouring.

### Lesson 96 — Pet Show — Speaking
Verified SOW:
- Focus: I like / I don't like / What about you?
- Main skill: Speaking / likes-dislikes.
- Complementary: Listening for details.
- Textbook: Superminds 1 p.37.

Engine behaviour:
- p.37 is source spine once exact content is verified.
- Oral preference exchange must dominate.
- Alternate formats: like/dislike corners, preference carousel, paired response cards.

### Lesson 97 — Pet Show — Listening
Verified SOW:
- Focus includes imperatives, adjectives amazing/clever, phrase I've got an idea.
- Main skill: Listening prediction.
- Complementary: Listening to very short narrative.
- Textbook: Superminds 1 pp.38–39.
- Value: bravery.

Engine behaviour:
- Prediction must precede narrative listening.
- Preserve story continuity across pp.38–39.
- Do not invent exact story details until page content is extracted.
- PBD evidence: prediction + identified story details.

### Lesson 98 — Pet Show — Reading
Verified SOW:
- Recycles language from Lesson 97 story.
- Main skill: Reading / blending.
- Complementary: Reading / segmenting.
- Textbook: Superminds 1 p.39.

Engine behaviour:
- Link explicitly to Lesson 97 story/source.
- Add continuity key: linked_previous_lesson = 97.
- Decoding must use verified story vocabulary.
- Do not swap in unrelated phonics words.

### Lesson 99 — Pet Show — Writing
Verified SOW:
- Recycles classroom objects + animals.
- Main skill: Writing / likes-dislikes.
- Complementary: Writing with and.
- Textbook: Superminds 1 p.40.

Engine behaviour:
- Written output should include connected information using and where appropriate.
- p.40 is source spine once exact content is verified.
- Alternate formats: two-item preference sentence, mini caption pair, classify-and-write.

### Lesson 100 — Pet Show — Language Arts
Verified SOW:
- Main/complementary focus: enjoy/respond to animal song.
- SOW uses listening, actions, joining in, group picture or remembered words/sentence, then personal response.

Engine behaviour:
- Song/performance route is required.
- Follow-up may be visual or short written response, but worksheet should not dominate.
- Preserve personal response to song/tune/animals.
- If a copyrighted song source is used, do not reproduce lyrics in generated material; use reference metadata and original response tasks only.


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 101–110

### Lesson 101 — Pet Show — Listening
Verified SOW:
- Recycles animals, prepositions, colours, adjectives; introduces/uses "It goes".
- Main skill: Listening to a very short narrative.
- Complementary: Speaking / naming-describing.
- SOW uses a park/garden picture, animal naming, a short route story across 5 locations, sequencing 1–5, repeated listening and pupil-created mini stories.

Engine behaviour:
- Narrative listening + route sequencing must be observable.
- Repetition is allowed for support.
- Speaking extension may transfer story creation to pupils.
- Alternate formats: listen-and-number route, animal journey map, sequence cards.
- Do not make pupils invent new story content before they have completed listening evidence.

### Lesson 102 — Pet Show — Speaking
Verified SOW:
- Recycles animal vocabulary, I like/don't like, What about you?
- Main skill: Speaking to find out basic personal information.
- Complementary: Listening to supported questions.
- SOW uses small-group preference grid, happy/sad faces, peer questioning and a bar chart summary.

Engine behaviour:
- Oral interview remains primary.
- Grid/chart is evidence/support, not the speaking objective itself.
- Suitable variation: mini preference poll, speaking tally cards, group survey + oral report.
- Preserve cooperative data collection.

### Lesson 103 — Pet Show — Reading
Verified SOW:
- Recycles animals, likes, numbers; adds lives in / doesn't like.
- Main skill: Reading for specific information/details.
- Complementary: Listening for details.
- SOW uses short profile texts, a whole-class model grid, then group jigsaw-style reading to solve a second information grid.

Engine behaviour:
- Reading detail retrieval must be explicit.
- Strong route: model one profile -> complete shared grid -> independent/group profile reading -> solve grid.
- Alternate formats: profile matching, information hunt, clue cards.
- Do not substitute a vocabulary worksheet for the text-reading task.

### Lesson 104 — Pet Show — Writing
Verified SOW:
- Recycles animal vocabulary + I like/don't like.
- Main skill: Writing likes/dislikes.
- Complementary: Writing basic personal information.
- SOW reuses bar-chart data from Lesson 102 and turns it into written statements, with digital or paper option.

Engine behaviour:
- Add continuity key: linked_previous_lesson = 102.
- Writing must interpret previously collected data.
- Digital output is optional; paper equivalent must remain available.
- Alternate formats: chart-to-sentence, class preference report, mini infographic captioning.

### Lesson 105 — Pet Show — Language Arts
Verified SOW:
- Reviews animals, colours, likes/dislikes, initial sounds and rhyming.
- Introduces/uses but / and.
- Main skill: imaginative response.
- Complementary: target-language sound recognition/reproduction.
- SOW uses short rhyming animal sentences and pair-created rhymes/chant-like lines.

Engine behaviour:
- Rhyming/sound play + creative language production are required.
- Use but/and only where suitable for pupil level.
- Alternate formats: rhyme cards, call-and-response animal lines, mini chant creation.
- Do not force extended writing; a short original line is enough.

### Lesson 106 — Pet Show — Writing
Verified SOW:
- Recycles animals, plurals, numbers and toys.
- Main skill: spelling familiar words.
- Complementary: Listening to supported classroom instructions.
- Textbook: Superminds 1 p.41.
- SOW provides explicit no-Workbook fallback using counted animal pictures and number-word writing.

Engine behaviour:
- Mark as WORKBOOK_EXPECTED_OR_FALLBACK.
- If workbook mapping exists, use it; otherwise use verified SOW fallback.
- Spelling/plural-word accuracy is primary evidence.
- Alternate CikguLaju follow-up must differ from simple count-and-write format.

### Lesson 107 — Pet Show — Speaking
Verified SOW:
- Focus: camouflage, snake, crocodile, butterfly, tiger, giraffe, grass, leaf, ground.
- Main skill: Speaking / naming-describing.
- Complementary: Listening to supported questions.
- Textbook: Superminds 1 p.42.
- Cross-curricular element: environmental sustainability.

Engine behaviour:
- p.42 is source spine once exact page content is verified.
- Speaking about animals/camouflage must dominate.
- Listening supports teacher/peer questioning.
- Suitable variation: describe-where-it-hides, camouflage picture talk, environment guessing.
- Preserve environmental context when it appears in verified source.

### Lesson 108 — Pet Show — Reading
Verified SOW:
- Focus includes leaves, tall grass.
- Main skill: Reading using visuals/high-frequency patterns.
- Complementary: Reading / blending.
- Textbook: Superminds 1 p.43.
- SOW notes blending words are content words from the Thinking Skills task "Where do the animals hide?"

Engine behaviour:
- Use ONLY verified content words from mapped p.43/Thinking Skills task for decoding.
- Visual support + blending must both be visible.
- Alternate formats: picture-to-sentence match, hide-location reading hunt, content-word blending cards.
- Do not inject unrelated phonics vocabulary.

### Lesson 109 — Pet Show — Listening
Verified SOW:
- Focus includes imperatives and body/mask vocabulary.
- Main skill: Listening to very short narrative.
- Complementary: Listening for specific details.
- Textbook: Superminds 1 p.44.

Engine behaviour:
- p.44 is source spine once exact content is verified.
- Listening should require understanding of sequence/details, not just vocabulary recall.
- Alternate formats: listen-and-sequence, instruction-picture match, story detail selection.
- Avoid inventing exact craft/narrative steps until page content is extracted.

### Lesson 110 — Pet Show — Language Arts
Verified SOW:
- Focus: camouflage / X hides in...
- Main skill: imaginative art-craft response.
- Complementary: Listening for specific information/details.
- SOW uses a hide-location quiz, realia/natural materials, teacher sentences, placing animal pictures, collage creation, written sentence and environmental discussion.

Engine behaviour:
- Environmental/natural-world context is integral.
- Required route: recall/predict -> listen/place -> create collage/product -> write short sentence -> share/discuss.
- Use locally available safe natural materials where practical.
- Do not reduce this to a colouring worksheet.


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 111–130

### Lesson 111 — Pet Show — Listening
- Recycles animals, plurals, numbers; focus "There are ..."
- Main: Listening for specific details; Complementary: Speaking naming/describing.
- SOW uses a six-box "perfect zoo" grid, teacher model, pupil-designed zoos and peer information exchange.
Engine:
- Listening-to-grid accuracy must be visible.
- Speaking extension may use pupil-created zoo descriptions.
- Alternate formats: zoo map, number-animal matrix, listen-and-place.

### Lesson 112 — Pet Show — Speaking
- Recycles imperatives/animals from Lesson 109 and explicitly adapts the p.44 action story.
- Main: Speaking; Complementary: asking for help.
- Pupils create a new action story from a frame and perform it while other groups mime.
Engine:
- Add continuity key: linked_previous_lesson = 109.
- Oral performance is mandatory even if pupils draft in writing.
- Preserve adaptation-vs-original comparison.
- Alternate formats: action-story cards, scene swap, group command story.

### Lesson 113 — Pet Show — Reading
- Recycles Lessons 107–109.
- Main: Reading using visuals; Complementary: Writing with "and".
- Uses Superminds p.42, true/false sentences, false-sentence rewriting, then pupils' Lesson 110 camouflage collages.
- Explicitly continues into Lesson 114.
Engine:
- Add continuity keys: linked_previous_lesson = 110; linked_next_lesson = 114.
- Reading source should include p.42 and pupil collage evidence.
- Alternate formats: read-and-correct, visual sentence audit, true/false correction cards.

### Lesson 114 — Pet Show — Writing
- Continues from Lesson 113.
- Main: plan/write words and phrases; Complementary: spelling.
Engine:
- Must consume the true/false/collage material prepared in Lesson 113.
- Add continuity key: linked_previous_lesson = 113.
- Writing should culminate in corrected/expanded statements about pupils' own camouflage product.
- Do not start with unrelated new content.

### Lesson 115 — Pet Show — Language Arts
- Reviews animal vocabulary/prepositions through song/chant.
- Uses "Five Little Monkeys" style counting/action pattern, then group-created animal versions and performance.
- Environmental discussion may follow.
Engine:
- Song/chant participation + imaginative adaptation required.
- Do not reproduce copyrighted lyrics; store source reference/pattern only.
- Alternate formats: animal action chant, number-animal performance, call-and-response.
- Preserve environmental reflection where appropriate.

### Lesson 116 — Pet Show — Writing
- Recycles toys, animals, prepositions, numbers, colours.
- Main: spelling; Complementary: picture-dictionary use.
- Textbook: Superminds p.45.
- Explicit no-Workbook fallback with animal flashcards and picture dictionary.
Engine:
- Mark WORKBOOK_EXPECTED_OR_FALLBACK.
- Use verified animal set if Workbook unavailable.
- Generated follow-up must differ from picture-dictionary matching.
- Alternate formats: category-and-spell, label grid, missing-letter animal bank.

### Lesson 117 — Lunchtime — Speaking
- New topic: Lunchtime.
- Food vocabulary: banana, cake, cheese, sandwich, apple, pizza, sausage, chicken, steak, peas, carrots.
- Main: Speaking naming/describing; Complementary: Listening main idea.
- Textbook: Superminds p.46.
Engine:
- p.46 is source spine once exact page content is verified.
- Speaking production with food vocabulary must dominate.
- Alternate formats: lunch tray talk, food-card carousel, "What's for lunch?" pair response.

### Lesson 118 — Lunchtime — Reading
- Focus: I've got / I haven't got + food vocabulary.
- Main: Reading using visuals/patterns; Complementary: Speaking basic personal info.
- Textbook: Superminds p.47.
Engine:
- Reading of visual-supported food statements required.
- Speaking personalisation follows reading.
- Alternate formats: read-and-pack, lunchbox match, have/haven't profile cards.

### Lesson 119 — Lunchtime — Listening
- Focus includes kitchen, milk, juice and imperatives.
- Main/complementary: Listening for specific detail.
Engine:
- Listening sequence/detail must be explicit.
- Use only verified lesson focus until exact page/source content is extracted.
- Alternate formats: listen-and-sequence, kitchen item selection, detail grid.

### Lesson 120 — Lunchtime
Verified SOW entry falls within Lunchtime progression.
Engine:
- Preserve exact skill/standards and textbook mapping from the SOW when content pack is populated.
- Do not infer page/task from neighbouring lessons.
- If exact source detail is missing, mark PARTIAL rather than invent.

### Lesson 121 — Lunchtime
Verified SOW entry within same topic sequence.
Engine:
- Use Lesson-specific skill and language focus from SOW.
- Maintain textbook/content-first grounding and alternate-format rule.
- No generic substitution.

### Lesson 122 — Lunchtime
Verified SOW entry within same topic sequence.
Engine:
- Keep main skill dominant and textbook/task relationship explicit.
- Preserve food-context continuity.

### Lesson 123 — Lunchtime
Verified SOW entry within same topic sequence.
Engine:
- Continue food-language progression.
- If workbook/source task exists, transform format rather than duplicate.

### Lesson 124 — Lunchtime — Writing / Recipe-style Production
Verified SOW excerpt:
- Uses pictures/toys of food including pizza.
- Pupils mime stages, teacher elicits/writes stages, highlights food words, then pairs write a new pizza recipe using different toppings and perform it.
Engine:
- Route: model/mime -> extract sequence -> write adapted recipe -> mime/say recipe.
- Final writing must be procedural/sequence-based.
- Alternate format: recipe cards, step ordering + rewrite, visual instruction strip.
- Do not copy source recipe verbatim.

### Lesson 125 — Lunchtime — Language Arts
- Focus: Do you like X? Yes/No; I've got X on/in/with my Y.
- Reviews song from textbook p.48.
- Pupils create a Crazy Food Poster and share likes/dislikes.
Engine:
- p.48 song is source reference; do not reproduce lyrics.
- Product + short writing + personal response are valid components.
- Alternate products: crazy sandwich card, food combination menu, illustrated caption.
- Preserve creativity without unrelated vocabulary.

### Lesson 126 — Lunchtime — Speaking
- Recycled food vocabulary.
- Main: Speaking to find out basic personal information; Complementary: Listening details.
- Textbook: Superminds p.49.
Engine:
- p.49 is source spine once exact content verified.
- Pair questioning/interview should dominate.
- Alternate formats: lunch preference interview, fridge survey, food-choice carousel.

### Lesson 127 — Lunchtime — Listening
- Focus: Where's (Misty)? Please, Hot, What have you got?
- Main: Listening details; Complementary: Reading main idea.
- Textbook: Superminds pp.50–51.
- Value: waiting your turn.
Engine:
- Preserve story/source continuity across pp.50–51.
- Listening remains primary.
- Do not invent exact narrative content until page text is extracted.
- Reading support should use same mapped story context.

### Lesson 128 — Lunchtime — Writing
- Recycles Lessons 126–127; fruit; Have you got any...? Yes/No.
- Main: plan/write words/phrases; Complementary: spelling.
- Uses p.49 picture, pupil-drawn fridge, 5 foods, written partner questions, written answers and peer checking.
Engine:
- Strong route: source picture -> own fridge -> write questions -> exchange -> answer -> peer check.
- Alternate formats: fridge inventory card, pantry checklist, pair Q&A sheet.
- Writing evidence must be visible.

### Lesson 129 — Lunchtime — Reading
- Focus: Sorry, stop, shop, hot dog.
- Main: Reading for specific detail; Complementary: target sound recognition/reproduction.
- Textbook: Superminds p.51.
- Value: waiting your turn.
Engine:
- Reading + phonological support should use verified p.51 vocabulary.
- Do not substitute unrelated phonics words.
- Alternate formats: sound-detail match, read-and-highlight, minimal sound sorting using verified words.

### Lesson 130 — Lunchtime — Language Arts
- Main: personal response to literary text; Complementary: Listening to very short narrative.
- SOW asks for a story with moral/message where possible, possibly linked to food / I've got / waiting turn / /ɒ/.
- The chosen story may be reviewed again in Lesson 140.
Engine:
- Save story/source continuity metadata for possible Lesson 140 reuse.
- Add continuity key: linked_future_lesson = 140 when the same story is selected.
- Route: prepare vocabulary -> interactive story listening -> artistic/motor follow-up -> discuss language/value.
- Do not force a specific copyrighted story; use teacher-selected verified source metadata.


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 131–150

### Lesson 131 — Lunchtime — Listening
- Recycles food vocabulary; introduces mouse, yummy.
- Main: Listening prediction; Complementary: Listening for details.
- SOW story: big mouse/small mouse, hospitality/politeness, food sharing.
Engine:
- Prediction must precede story.
- Build story details from repeated listening using keywords/pictures.
- Values discussion may use L1 where appropriate.
- Alternate formats: story-sequence cards, food-detail grid, retell picture chain.
- Do not reproduce copyrighted storybook text; this SOW-provided classroom story may be represented as structured content only.

### Lesson 132 — Lunchtime — Speaking
- Food shop role-play: Have you got any...? How much are...? Here you are.
- Main: Speaking social phrases; Complementary: Listening questions.
- Uses food cards, prices, optional toy money; financial education.
Engine:
- Every pupil should act as customer and shopkeeper.
- Oral dialogue is primary; copied dialogue is follow-up only.
- Alternate formats: mini market stalls, menu-price carousel, buyer/seller cards.
- Preserve polite greetings/thanks.

### Lesson 133 — Lunchtime — Reading
- Food vocabulary.
- Main: Reading/blending; Complementary: spelling.
- Uses plastic letters, scrambled food words in sentences, grid completion.
Engine:
- Explicit decoding + spelling required.
- If source uses scrambled words, CikguLaju follow-up should use a different format.
- Alternate formats: phoneme build, picture-to-word decode, food word sorting.

### Lesson 134 — Lunchtime — Writing
- Recycles food vocabulary.
- Main: spelling; Complementary: blending.
- Pupils create their own food anagram puzzle with pictures, then exchange.
Engine:
- Writing/spelling product must be pupil-created.
- Alternate formats: word maze, label-and-hide, missing-letter puzzle.
- Do not repeat exact anagram mechanics if already used in the source lesson.

### Lesson 135 — Lunchtime — Language Arts
- Focus: Have you got...? Yes/No; polite canteen/menu interaction.
- Reviews school canteen vocabulary from p.50 and dialogue patterns from pp.50–51.
- Pupils create menus and role-play with new partners.
Engine:
- Product (menu) + oral role-play + politeness are all required.
- Alternate product: mini canteen card, café board, lunch menu strip.
- Do not copy source dialogue verbatim; preserve function and verified language frames.

### Lesson 136 — Lunchtime — Listening
- Numbers 11–20.
- Main: Listening for specific details; Complementary: spelling.
- Textbook: Superminds p.52.
Engine:
- p.52 is source spine once exact page content is verified.
- Listening evidence on numbers must be explicit.
- Alternate formats: listen-and-circle number, number-food match, dictation grid.

### Lesson 137 — Lunchtime — Reading
- Food vocabulary + numbers 11–20.
- Main: Reading using visuals/patterns; Complementary: Speaking.
- Textbook: Superminds p.53.
Engine:
- Reading of number/food combinations should lead to speaking personalisation.
- Alternate formats: visual number-food hunt, read-and-say cards, quantity matching.

### Lesson 138 — Lunchtime — Speaking
- Fruit/vegetable vocabulary including broccoli, onions, mushrooms, potatoes, corn, peaches, pineapples, pears, oranges, coconuts, tomatoes, strawberries.
- Main: Speaking likes/dislikes; Complementary: word-level reading.
- Textbook: Superminds p.54.
- SOW provides no-sticker fallback using handwritten word slips.
Engine:
- Speaking remains primary.
- Sticker fallback is source-access support, not a new learning target.
- Alternate formats: market-preference speaking, fruit/veg category talk, like/dislike carousel.

### Lesson 139 — Lunchtime — Writing
Verified SOW entry in Lunchtime sequence.
Engine:
- Populate exact skill/content/page from SOW before runtime generation.
- Preserve food-topic continuity.
- If exact source task is not yet extracted, mark PARTIAL and avoid invented details.

### Lesson 140 — Lunchtime — Language Arts
Verified as story-review point linked from Lesson 130 when the same story is selected.
Engine:
- Add continuity key: linked_previous_lesson = 130 when applicable.
- Reuse the same verified story/source rather than silently substituting a new one.
- Route: recall -> reread/listen -> extend -> personal/creative response.

### Lesson 141 — Lunchtime
Verified SOW entry in topic sequence.
Engine:
- Use exact SOW skill/focus/content pack.
- Maintain textbook/workbook grounding and alternate-format rule.
- No generic substitution.

### Lesson 142 — Lunchtime
Verified SOW entry.
Engine:
- Preserve lesson-specific main/complementary skill and source linkage.
- Do not infer page/task from adjacent lessons.

### Lesson 143 — Lunchtime — Reading/Maths-integrated problem context
Verified SOW excerpt:
- Uses food/price information and maths language around spending, addition/multiplication.
- Provides model word problems later reused in Lesson 144.
Engine:
- Reading comprehension of the problem text precedes calculation.
- Save problem-model continuity for Lesson 144.
- Alternate formats: read-and-match price problem, visual shopping problem, clue-card maths reading.

### Lesson 144 — Lunchtime — Writing
- Recycles food vocabulary; uses spends, times...is..., and.
- Main: plan/write words/phrases; Complementary: connect with and.
- Pupils review Lesson 143 problems, then write their own and exchange/solve.
Engine:
- Add continuity key: linked_previous_lesson = 143.
- Writing of original word problems is mandatory.
- Financial-education context should be preserved.
- Alternate format: price-card problem writing, mini market challenge.

### Lesson 145 — Lunchtime — Language Arts
- Focus: I've got / I haven't got.
- Main: personal response; Complementary: Reading/blending.
- Uses fridge + shopping-list deductive reasoning, then pupil fridge/list worksheet and partner speaking.
Engine:
- Deductive reasoning from shopping list vs fridge is core.
- Reading must contribute to inference.
- Alternate formats: pantry logic, lunchbox checklist, fridge mystery.
- Avoid reducing to vocabulary matching.

### Lesson 146 — Lunchtime — Speaking
- Recycled food vocabulary; where food grows: on the ground, in trees, on plants.
- Main: Speaking; Complementary: Reading visuals/patterns.
- Textbook: Superminds p.55.
- No-Workbook fallback provides fruit/vegetable categorisation + where-it-grows task.
Engine:
- Mark WORKBOOK_EXPECTED_OR_FALLBACK.
- Preserve science/technology link.
- Speaking about food location/growth should be visible.
- Alternate formats: grow-location sorting talk, garden map explanation, produce-category speaking.

### Lesson 147 — Lunchtime — Writing
- Recycles toys, food, imperatives.
- Main: Writing basic personal information; Complementary: Reading details.
- Textbook: Superminds p.56.
- No-Workbook fallback uses a monster/sandwich poster and detail grid.
Engine:
- Mark WORKBOOK_EXPECTED_OR_FALLBACK.
- Written completion of name/colour/sandwich details is primary.
- Alternate formats: monster profile card, sandwich ingredient caption, read-and-complete.

### Lesson 148 — Lunchtime — Reading
- Topic review.
- Main: picture-dictionary use; Complementary: Speaking personal info.
- Textbook: Superminds p.57.
- No-Workbook fallback uses lunchtime flashcards and picture dictionary.
Engine:
- Mark WORKBOOK_EXPECTED_OR_FALLBACK.
- Picture-dictionary navigation must be explicit.
- Alternate formats: category hunt, find-list-say, picture-dictionary scavenger task.

### Lesson 149 — Lunchtime — Listening
- Focus: healthy/unhealthy + recycled food.
- Main: Listening prediction; Complementary: Listening details.
- SOW uses healthy/unhealthy sorting, predicts foods in a short text, completes grid, then rewrites choices to make all meals healthy.
- Global sustainability / wellbeing context.
Engine:
- Prediction must precede listening.
- Listening grid is evidence spine.
- Follow-up transformation from unhealthy to healthy must stay grounded in source foods.
- Alternate formats: healthy-food listening chart, meal makeover cards, listen-and-classify.

### Lesson 150 — Lunchtime — Language Arts
- Theme: healthy eating.
- Main: personal response to literary text; Complementary: Listening narrative.
- Can use a healthy-eating story/text/poem or responses to p.55 food diary.
Engine:
- Healthy-eating message + personal response are central.
- Encourage pupils to talk/write about their own eating habits.
- Source may be p.55 or another verified teacher-selected text.
- Do not moralise beyond age-appropriate balanced-diet messaging.


## PRIMARY YEAR 1 ENGLISH — VERIFIED LESSON EXEMPLARS 151–160

### Lesson 151 — Year 1 Revision — Listening
- Revises all Year 1 topics: Friends, At School, Let's Play!, Pet Show, Lunchtime.
- Main: Listening to supported questions; Complementary: Speaking / naming-describing.
- SOW uses a noughts-and-crosses revision grid with topic questions, "Correct it!", "Listen and do", and mixed revision prompts.
Engine:
- Treat as cumulative retrieval, not new content.
- Questions must be drawn only from verified Year 1 content.
- Listening response must remain observable.
- Alternate format: team quiz board, category wheel, topic challenge cards.
- Avoid introducing unverified vocabulary.

### Lesson 152 — Year 1 Revision — Speaking
- Main: Speaking / naming-describing; Complementary: Listening to supported questions.
- Uses Superminds pages as visual prompts; pupils create and ask their own revision questions.
Engine:
- Textbook pages act as verified visual retrieval prompts.
- Pupils should both ask and answer.
- Alternate formats: picture-question carousel, group quiz cards, page-hunt speaking challenge.
- Do not make teacher questioning the only speaking evidence.

### Lesson 153 — Year 1 Revision — Reading
- Main: Reading for specific details; Complementary: Speaking.
- SOW uses a Year 1 revision board game, dice/counters, topic squares and free-question squares.
- Includes reflection on cooperation and handling language/content challenges.
Engine:
- Reading of instructions/prompts is the task spine.
- Speaking response follows the square/prompt.
- Reflection may use L1 where the focus is metacognition/cooperation.
- Alternate formats: revision path game, reading challenge board, topic mission cards.

### Lesson 154 — Year 1 Revision — Writing
- Main: Writing using "and"; Complementary: Reading details.
- Uses 24–30 Year 1 vocabulary pictures, sentence frames "A ___ and a ___ are..." / "have got...", group connection generation, true/false sentence writing and peer correction.
Engine:
- Connection-making across known vocabulary is required.
- Written true/false set + peer correction is primary evidence.
- Alternate formats: connection cards, classify-and-connect, two-item fact sentences.
- Do not add vocabulary outside verified Year 1 bank.

### Lesson 155 — Year 1 Revision — Language Arts
- Main: imaginative response; Complementary: Speaking to audience.
- Matches textbook units to themes, brainstorms language by unit, checks textbook, presents, then writes unit-based dialogues for later performance.
- Explicitly prepares Lesson 160.
Engine:
- Add continuity key: linked_next_lesson = 160.
- Dialogue writing must be based on verified unit language.
- Teacher feedback/self-correction should occur before performance lesson.
- Do not copy supplied dialogue examples wholesale.

### Lesson 156 — Year 1 Revision — Listening
- Main: Listening to supported questions; Complementary: Speaking to find out personal information.
- Uses "Find a friend who..." grid with Year 1 language, then pupils create their own grid.
Engine:
- Listening + oral interaction are both required.
- Pupil-created prompts must stay within verified language.
- Alternate formats: mingle grid, peer-find cards, group question hunt.
- Grid construction is extension, not substitute for listening/speaking.

### Lesson 157 — Year 1 Revision — Speaking
- Main: Speaking basic personal information; Complementary: Listening for details.
- Uses "Me and my friends" grid: age, siblings, favourite food/animal/toy.
- Pupils exchange information and report an interesting group connection.
Engine:
- Oral exchange and third-person reporting are required.
- Alternate formats: mini profile exchange, friend fact cards, compare-and-report.
- Written grid is support only.

### Lesson 158 — Year 1 Revision — Writing
- Main: spelling familiar high-frequency words; Complementary: Reading using visuals/patterns.
- Pupils create an ABC poster of Year 1 vocabulary using Superminds as reference.
- Posters and word slips are intentionally saved for Lesson 159.
Engine:
- Add continuity key: linked_next_lesson = 159.
- Only verified Year 1 vocabulary may be used.
- Writing/spelling accuracy must be checked.
- Preserve reusable-BBM logic: poster becomes next-lesson reading material.

### Lesson 159 — Year 1 Revision — Reading
- Main: Reading simple word-level games; Complementary: Reading using visuals/patterns.
- Explicit continuation of Lesson 158 ABC posters/word slips.
- Groups swap posters and match words to pictures; then Listen-and-Point review.
Engine:
- Add continuity key: linked_previous_lesson = 158.
- Must reuse Lesson 158 artefacts where available.
- Alternate format: poster exchange, word-picture relay, category match.
- Do not generate a fresh unrelated word set.

### Lesson 160 — Year 1 Revision — Language Arts
- Final Year 1 lesson.
- Main: imaginative response; Complementary: Speaking to audience.
- Pupils revise dialogues from Lesson 155 using teacher feedback, practise, introduce themselves, then perform to an audience.
Engine:
- Add continuity key: linked_previous_lesson = 155.
- Performance must use the previously prepared/revised dialogues.
- Props are optional; audience may be class/parents/staff/other classes subject to permission.
- Do not silently replace dialogues with newly generated unrelated scripts.
- This lesson closes the Year 1 sequence; mark YEAR1_SEQUENCE_COMPLETE once source QA passes.
