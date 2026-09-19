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


## PRIMARY YEAR 2 ENGLISH — VERIFIED STARTER / FREE TIME EXEMPLARS 1–3

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary source cross-check: Primary Year 2 SK Scheme of Work (Lessons 1–160).

### Lesson 1 — Introduction — Writing
Verified SOW:
- Theme: World of Self, Family & Friends.
- Topic: Introduction.
- Language focus: review of present simple to describe self.
- Main skill: Writing 4.2 / LS 4.2.1 ask for and give basic personal information using basic questions/statements.
- Complementary: Speaking 2.3 / LS 2.3.1 introduce self and others to an audience using fixed phrases.
- SOW proposes Year 1 review: pupils ask/answer about name, age and favourites; write about a partner ("My new friend"); draw a supporting picture; introduce partner to class.

Engine behaviour:
- Use this as a diagnostic/revision lesson, not new grammar teaching.
- Written partner profile is primary evidence.
- Speaking presentation follows the written profile.
- Alternate CikguLaju formats: friend profile card, interview-to-mini-poster, partner fact file.
- Do not invent unsupported profile fields beyond verified personal information.

### Lesson 2 — Free Time — Listening
Verified SOW:
- Theme: World of Self, Family and Friends.
- Topic: Free Time.
- Language focus: days of the week; It's (day); On + day.
- Main skill: Listening 1.2 / LS 1.2.1 understand with support the main idea of simple sentences.
- Complementary: Speaking 2.1 / LS 2.1.1 give simple personal information using basic statements.
- Textbook reference: Superminds 1 p.58.

Engine behaviour:
- p.58 is source spine once exact page content is verified.
- Listening for overall meaning/day reference must precede speaking.
- Speaking extension should personalise routine/day information.
- Alternate formats: listen-and-point weekday strip, day-choice cards, routine-day response grid.
- Do not invent exact textbook dialogue/activity before page extraction.

### Lesson 3 — Free Time — Speaking
Verified SOW:
- Theme: World of Self, Family and Friends.
- Topic: Free Time.
- Language focus: days of the week; present simple for regular activities (I + verb + on + day).
- Main skill: Speaking.
- Verified SOW sequence continues directly from Lesson 2 / Free Time.

Engine behaviour:
- Oral production of regular activities + day is the evidence spine.
- Reuse verified weekday language from Lesson 2.
- Suitable alternates: weekly routine carousel, day/activity cards, pair schedule talk.
- Keep content within verified Free Time vocabulary once textbook page/content is mapped.


## PRIMARY YEAR 2 ENGLISH — VERIFIED FREE TIME EXEMPLARS 4–10

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-checks: Primary Year 2 SK Scheme of Work / SJK Scheme of Work mirrors.

### Lesson 4 — Free Time — Reading
Verified SOW:
- Theme: World of Self, Family and Friends.
- Topic: Free Time.
- Language focus: present simple; "On (day) we (verb)."
- Main skill: Reading.
- Textbook reference: Superminds 1 p.60.
- SOW excerpt shows phonics/word recognition work using familiar Free Time vocabulary.

Engine behaviour:
- p.60 is source spine once exact page content is extracted.
- Reading/decoding is primary evidence.
- Alternate formats: read-and-match day/activity phrases, phoneme-word sort, picture-supported sentence match.
- Do not invent exact textbook task before page verification.

### Lesson 5 — Free Time — Writing
Verified SOW sequence:
- Continues Free Time language with present simple and day/activity combinations.
- Main skill: Writing.
- SOW uses sentence-building support with word cards and explicit attention to sentence punctuation.
- Pupils write about their favourite day and what they do on that day.

Engine behaviour:
- Sentence construction and punctuation should be explicit.
- Alternate formats: day-routine sentence strips, favourite-day mini card, reorder-and-write.
- Keep personalisation grounded in verified Free Time language.

### Lesson 6 — Free Time — Language Arts
Verified SOW progression places a Language Arts lesson after initial Free Time skills cycle.
Engine behaviour:
- Use verified Free Time vocabulary/language only.
- Product/performance should be creative but still tied to lesson language.
- If exact source text/song is not yet extracted, mark CONTENT_DETAIL_PENDING and avoid invented lyrics/text.

### Lesson 7 — Free Time — Listening
Verified SOW sequence:
- Returns to Free Time with listening focus.
- Recycles days and regular-activity language.
Engine behaviour:
- Listening evidence must involve identifying day/activity information.
- Alternate formats: listen-and-tick timetable, day/activity grid, sequence cards.
- Preserve recycling role; no unnecessary new vocabulary.

### Lesson 8 — Free Time — Speaking
Verified SOW sequence:
- Speaking focus on personal Free Time information.
- Recycles regular activities and day expressions.
Engine behaviour:
- Pair/group oral exchange should dominate.
- Alternate formats: weekly routine interview, find-someone-who, routine carousel.
- Avoid worksheet-dominant delivery.

### Lesson 9 — Free Time — Reading
Verified SOW sequence:
- Reading focus within same topic cycle.
Engine behaviour:
- Read short familiar phrases/sentences for detail.
- Use visuals and known language where source supports it.
- Alternate formats: read-and-sort, timetable reading, sentence-picture matching.

### Lesson 10 — Free Time — Writing
Verified SOW sequence:
- Writing focus within Free Time cycle.
Engine behaviour:
- Pupils produce simple sentences based on verified language already practised.
- Alternate formats: guided weekly plan, sentence completion-to-free write, mini routine profile.
- Require spelling/punctuation check.


## PRIMARY YEAR 2 ENGLISH — VERIFIED FREE TIME EXEMPLARS 11–20

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-check: Primary Year 2 SK Scheme of Work.

### Lesson 11 — Free Time — Speaking
Verified SOW:
- Language: Do you...? Yes, I do. / No, I don't.
- Main: Speaking 2.1.1 give simple personal information.
- Complementary: Speaking 2.1.2 ask basic questions.
- Textbook: Superminds 1 p.61.

Engine behaviour:
- Pair questioning must dominate.
- Suitable alternates: weekend-activity survey, yes/no speaking grid, routine interview cards.
- Keep question-answer pattern explicit.

### Lesson 12 — Free Time — Listening
Verified SOW:
- Language includes: We're lost; lake; wait and see; come with me; thank you very much.
- Main focus: Listening.
- Textbook: Superminds 1 pp.62–63.
- SOW notes Activity 1 is a picture story continuing onto p.63.
- Value: asking for help when needed.

Engine behaviour:
- Preserve picture-story continuity across pp.62–63.
- Listening for story meaning/details must be primary.
- Do not invent missing story details beyond verified page mapping.
- Suitable alternates: picture-sequence listening, story detail cards, listen-and-order.

### Lesson 13 — Free Time — Reading
Verified SOW:
- Recycles story language from the preceding story sequence.
- Main: Reading 3.1.3 blend phonemes (CVC, CCVC, CVCV, CCV).
- Complementary: Listening 1.1.1 reproduce high-frequency phonemes.
- Textbook: Superminds 1 p.63.

Engine behaviour:
- Link to Lesson 12 story vocabulary.
- Add continuity key: linked_previous_lesson = 12.
- Use only verified story/content words for decoding.
- Alternate formats: blend-and-match, phoneme build, story-word decoding cards.

### Lesson 14 — Free Time — Writing
Verified SOW:
- Language: How many days do...? + possessive 's.
- Main: Writing 4.3.1 capital letters/full stops in guided writing.
- Complementary: Listening 1.2.2 specific details.
- Textbook: Superminds 1 p.64.

Engine behaviour:
- Guided sentence accuracy and punctuation are core.
- Listening may supply information that pupils convert into written sentences.
- Alternate formats: listen-note-write, possessive mini-profile, punctuation repair.

### Lesson 15 — Free Time — Language Arts
Verified SOW:
- Phoneme blends CVC, CCVC, CVCV, CCV.
- Main: Language Arts 5.1.2 songs/chants/rhymes.
- Complementary: Reading 3.1.3 blending.
- SOW says design own LA lesson linked to standards and phoneme blending.

Engine behaviour:
- Song/chant + visible written words required.
- Reading/blending must connect to the same language.
- Do not reproduce copyrighted lyrics; use source metadata/pattern only.
- Alternate formats: phonics chant cards, blend-and-clap, action rhyme with verified words.

### Lesson 16 — Free Time — Listening
Verified SOW:
- Review/extension of recently introduced language and vocabulary.
- Main: Listening 1.2.2 specific details.
- Complementary: Reading 3.1.1 alphabet.
- SOW suggests extending listening from p.64; pair dictation of spelling/info.
- Review/extend pp.61–64.

Engine behaviour:
- Content should recycle Lessons 11–14.
- Strong route: listen -> record detail -> pair dictation -> verify spelling.
- Alternate formats: information-gap dictation, letter-detail grid, peer listening check.

### Lesson 17 — Free Time — Speaking
Verified SOW:
- Review/extension of recent language.
- Main: Speaking 2.1.2 ask basic questions.
- Complementary: Writing 4.2.1 ask/give personal information in writing.
- SOW suggests pupils prepare and run a survey about weekend activities.
- Findings can be reported in Lesson 19.

Engine behaviour:
- Add continuity key: linked_next_lesson = 19.
- Oral survey must be completed before report writing.
- Preserve weekend/free-time topic.
- Alternate formats: weekend survey grid, class poll, find-someone-who.

### Lesson 18 — Free Time — Reading
Verified SOW:
- Review/extension of recent language.
- Main: Reading 3.2.2 specific details.
- Complementary: Reading 3.2.3 reread to understand.
- SOW suggests reviewing pp.62–63 story by cutting it into stages and ordering sentences/pictures.
- Review/extend pp.61–64.

Engine behaviour:
- Reuse verified story from Lessons 12–13.
- Add continuity key: linked_previous_lessons = 12,13.
- Reading order/sequence evidence must be visible.
- Alternate formats: sequence strips, story jigsaw, read-and-order picture cards.

### Lesson 19 — Free Time — Writing
Verified SOW:
- Review/extension of recent language.
- Main: Writing 4.3.3 plan/draft/write simple sentences.
- Complementary: Writing 4.2.5 connect words/phrases with conjunctions.
- SOW suggests reporting findings from the Lesson 17 weekend survey, optionally digitally.

Engine behaviour:
- Add continuity key: linked_previous_lesson = 17.
- Writing must use actual survey data where available.
- Digital or paper output acceptable.
- Alternate formats: mini survey report, class findings poster, simple data-to-sentence task.

### Lesson 20 — Free Time — Language Arts
Verified SOW:
- Language: On day+s I + verb phrase.
- Main: Language Arts 5.1.2 simple songs/chants/rhymes.
- Complementary: Writing.
- Final LA lesson in this Free Time review cycle.

Engine behaviour:
- Creative performance must recycle verified weekday/free-time language.
- Written support may be a short original line/verse or day-activity caption.
- Avoid generic song activity unrelated to Free Time.


## PRIMARY YEAR 2 ENGLISH — VERIFIED FREE TIME / THE OLD HOUSE EXEMPLARS 21–30

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-check: Primary Year 2 SK Scheme of Work.

### Lesson 21 — Free Time — Reading
Verified SOW:
- Theme: World of Self, Family and Friends.
- Topic: Free Time.
- Language focus: recycled food + free-time activities; healthy, unhealthy, eat healthy food, keep fit, have fun.
- Main: Reading 3.2.2 understand specific information/details.
- Complementary: Speaking 2.1.2 ask basic questions.
- Textbook: Superminds 1 p.66.

Engine behaviour:
- Reading detail from p.66 is the evidence spine.
- Speaking extension may ask classmates about healthy/free-time habits.
- Alternate formats: healthy-habit read-and-sort, information hunt, read-and-ask cards.
- Do not turn into generic health education.

### Lesson 22 — Free Time — Speaking
Verified SOW:
- Recycles free-time activities and days of the week.
- Main skill: Speaking.
- Textbook-based continuation after p.66.

Engine behaviour:
- Oral discussion/questioning about free-time routine should dominate.
- Reuse verified day/activity language.
- Alternate formats: routine interview, weekend choices, free-time speaking carousel.
- Keep exact textbook task pending until page extraction.

### Lesson 23 — Free Time — Listening
Verified SOW sequence:
- Continues Free Time review/extension after p.66.
Engine behaviour:
- Listening detail must stay tied to verified free-time/health language.
- Alternate formats: listen-and-tick habits, routine grid, detail matching.
- Mark page/task detail pending if source page not directly extracted.

### Lesson 24 — Free Time — Writing
Verified SOW sequence:
- Writing focus in same Free Time review cycle.
Engine behaviour:
- Written output should reuse verified Free Time vocabulary and sentence patterns.
- Alternate formats: healthy/free-time mini profile, routine sentence set, poster captions.
- Spelling/punctuation accuracy required.

### Lesson 25 — Free Time — Language Arts
Verified SOW sequence:
- Language Arts within Free Time review cycle.
Engine behaviour:
- Creative product/performance must recycle verified Free Time/healthy-living language.
- Do not invent source text/song if not extracted.
- Suitable alternates: healthy habits chant, free-time rhyme, illustrated mini poster.

### Lesson 26 — Free Time — Listening
Verified SOW sequence:
- Listening review/extension of recently introduced language.
Engine behaviour:
- Use formative assessment gaps from Lessons 21–25.
- Alternate formats: targeted listen-and-identify, detail repair task, listening mini-quiz.
- No unrelated vocabulary expansion.

### Lesson 27 — Free Time — Speaking
Verified SOW sequence:
- Speaking review/extension.
Engine behaviour:
- Pair/group oral interaction should address identified language gaps.
- Alternate formats: survey, information gap, speaking challenge cards.

### Lesson 28 — Free Time — Reading
Verified SOW sequence:
- Reading review/extension.
Engine behaviour:
- Reuse familiar verified text/page language.
- Alternate formats: read-and-correct, sequence, information hunt.
- Avoid fresh unverified reading text if textbook material is available.

### Lesson 29 — Free Time — Writing
Verified SOW:
- Main: Writing 4.3.2 spelling familiar high-frequency words accurately.
- Complementary: Writing 4.3.1 capital letters and full stops.
- SOW suggests spelling revision games and writing sentences based on posters from p.69.
- Review/extend p.65–69.

Engine behaviour:
- Accuracy in spelling, punctuation and capitals is explicit QA evidence.
- Reuse p.69 poster/content once exact page extraction is available.
- Alternate formats: poster-to-sentence, error-correction writing, caption writing.
- Do not introduce unrelated sentence content.

### Lesson 30 — Free Time — Language Arts
Verified SOW:
- Theme: World of Self, Family and Friends.
- Topic: Free Time.
- Main: Language Arts 5.3.1 imaginative response.
- SOW asks teacher to design own Language Arts lesson linked to standards.
- Review/extend p.65–69.
- Cross-curricular focus includes citizenship/cooperation and healthy living.

Engine behaviour:
- Treat as consolidation/creative response to Free Time content.
- Product may be poster, chant/rap, role-play or other age-appropriate response.
- Must remain grounded in verified p.65–69 language/content.
- No invented copyrighted text.

## TRANSITION NOTE — YEAR 2
The next textbook unit after this Free Time cycle is **The Old House**. Source cross-checks show subsequent lessons use house vocabulary and structures such as "There's a..." / "There are..." and textbook p.71 onward. Do not merge the two units in runtime mapping.


## PRIMARY YEAR 2 ENGLISH — THE OLD HOUSE EXEMPLARS 31–40

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-check: Primary Year 2 SK Scheme of Work / textbook progression.

### Lesson 31 — The Old House — Listening
Verified progression:
- New unit transition into house vocabulary and descriptions.
- Main skill: Listening.
- Core structure set begins around "There's a..." / "There are...".
- Textbook progression moves into p.71 onward.

Engine behaviour:
- Listening should identify rooms/house objects/locations from verified source.
- Alternate formats: listen-and-point house plan, room/object grid, picture detail selection.
- Do not invent exact house-object list until page mapping is extracted.

### Lesson 32 — The Old House — Speaking
Verified progression:
- Recycles house vocabulary and "There's / There are".
- Main skill: Speaking.
Engine behaviour:
- Oral description of a room/house scene should dominate.
- Alternate formats: describe-the-room, spot-and-say, pair house-map talk.
- Keep language within verified unit vocabulary.

### Lesson 33 — The Old House — Reading
Verified progression:
- Reading focus using house/room content.
Engine behaviour:
- Visual-supported reading and detail matching required.
- Alternate formats: read-and-match room/object, house clue cards, sentence-picture match.
- Exact text content remains pending direct extraction.

### Lesson 34 — The Old House — Writing
Verified progression:
- Writing simple house/room statements.
- Core structures use singular/plural description.
Engine behaviour:
- Written sentences should distinguish "There's..." vs "There are...".
- Alternate formats: room captioning, house-label sentence set, picture-to-sentence writing.
- Require basic punctuation/spelling checks.

### Lesson 35 — The Old House — Language Arts
Verified progression:
- Language Arts lesson tied to house/home theme.
Engine behaviour:
- Creative response must reuse verified house language.
- Suitable alternates: house rhyme, room mini-book, house drawing + short captions.
- If exact source text/song is unavailable, mark CONTENT_DETAIL_PENDING.

### Lesson 36 — The Old House — Listening
Verified progression:
- Listening review/extension within unit.
Engine behaviour:
- Listen for object/location details.
- Alternate formats: house plan dictation, listen-and-place furniture, location grid.
- Avoid unrelated vocabulary expansion.

### Lesson 37 — The Old House — Speaking
Verified progression:
- Speaking review/extension of house descriptions.
Engine behaviour:
- Pair information-gap around room/house scene is suitable.
- Alternate formats: "What's in the room?" interview, hidden-room description, picture difference talk.

### Lesson 38 — The Old House — Reading
Verified progression:
- Reading for house/room detail.
Engine behaviour:
- Reading must involve specific detail, not only word recognition.
- Alternate formats: room clues, true/false house sentences, information hunt.

### Lesson 39 — The Old House — Writing
Verified progression:
- Writing review/extension.
Engine behaviour:
- Pupils write connected house/room descriptions using verified structures.
- Alternate formats: mini house profile, sentence repair, room description card.
- Preserve singular/plural accuracy.

### Lesson 40 — The Old House — Language Arts
Verified progression:
- Unit consolidation through creative/literary response.
Engine behaviour:
- Use only verified house/home vocabulary and structures.
- Product/performance should consolidate unit language.
- No invented copyrighted text.


## PRIMARY YEAR 2 ENGLISH — THE OLD HOUSE EXEMPLARS 41–50

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-check: Primary Year 2 SK Scheme of Work / textbook unit progression.

### Lesson 41 — The Old House — Listening
Verified progression:
- Continues The Old House unit.
- Main focus: Listening for specific details in house/room descriptions.
Engine behaviour:
- Use familiar room/object/location language only.
- Alternate formats: listen-and-mark room plan, object-location grid, detail bingo.
- Preserve continuity from Lessons 31–40.

### Lesson 42 — The Old House — Speaking
Verified progression:
- Speaking focus using house descriptions and location language.
Engine behaviour:
- Pupils ask/answer about what is in a room/house.
- Alternate formats: room interview, describe-and-draw, hidden-picture information gap.
- Ensure singular/plural structure remains accurate.

### Lesson 43 — The Old House — Reading
Verified progression:
- Reading focus in same unit.
Engine behaviour:
- Read short house descriptions for specific details.
- Alternate formats: read-and-draw, clue-to-room match, true/false/correct.
- Do not introduce unverified story content.

### Lesson 44 — The Old House — Writing
Verified progression:
- Writing focus using familiar house vocabulary.
Engine behaviour:
- Pupils produce simple room/house descriptions.
- Alternate formats: picture caption set, room fact file, guided paragraph frame.
- Check spelling, punctuation and singular/plural agreement.

### Lesson 45 — The Old House — Language Arts
Verified progression:
- Language Arts consolidation linked to home/house theme.
Engine behaviour:
- Creative product must recycle verified unit language.
- Suitable alternates: mini house book, room rhyme, simple role-play scene.
- Mark source-text detail pending if exact text/song unavailable.

### Lesson 46 — The Old House — Listening
Verified progression:
- Review/extension listening within the unit.
Engine behaviour:
- Target specific detail retrieval and location understanding.
- Alternate formats: house-map dictation, listen-and-place, compare two rooms.

### Lesson 47 — The Old House — Speaking
Verified progression:
- Review/extension speaking.
Engine behaviour:
- Encourage complete simple sentences about rooms/objects.
- Alternate formats: spot-the-difference, pair house tour, question-card exchange.

### Lesson 48 — The Old House — Reading
Verified progression:
- Review/extension reading.
Engine behaviour:
- Reading should require detail selection or inference from simple descriptions.
- Alternate formats: house clue hunt, sentence-to-picture match, sequencing of room clues.

### Lesson 49 — The Old House — Writing
Verified progression:
- Review/extension writing.
Engine behaviour:
- Use familiar unit language to produce a short coherent description.
- Alternate formats: my room card, house brochure panel, guided description.
- Preserve Year 2 sentence load; do not over-complexify.

### Lesson 50 — The Old House — Language Arts
Verified progression:
- Creative consolidation before transition to the next unit.
Engine behaviour:
- Performance/product may combine speaking + simple writing.
- Keep all language tied to The Old House content.
- No invented copyrighted source text.

## YEAR 2 QA STATUS AFTER LESSON 50
- Lessons 1–50 now have seed-bank entries.
- Exact textbook page/task details are fully explicit only where directly cross-checked.
- Entries without exact page extraction remain CONTENT_DETAIL_PENDING and must not be treated as exact textbook transcription.


## PRIMARY YEAR 2 ENGLISH — THE OLD HOUSE EXEMPLARS 51–60

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-check: Primary Year 2 SK Scheme of Work / textbook unit progression.

### Lesson 51 — The Old House — Listening
Verified progression:
- Continues The Old House unit with listening for room/object/location details.
Engine behaviour:
- Use known house vocabulary and positional language.
- Alternate formats: listen-and-place, room detail checklist, house-plan listening.

### Lesson 52 — The Old House — Speaking
Verified progression:
- Speaking focus within same unit.
Engine behaviour:
- Pair interaction around room contents/location.
- Alternate formats: describe-and-draw, hidden-room information gap, room interview.

### Lesson 53 — The Old House — Reading
Verified progression:
- Reading for specific detail in short house descriptions.
Engine behaviour:
- Alternate formats: clue-to-room match, read-and-correct, room information hunt.
- Keep source text within verified unit language.

### Lesson 54 — The Old House — Writing
Verified progression:
- Writing simple descriptive sentences about a room/house.
Engine behaviour:
- Reinforce singular/plural and basic punctuation.
- Alternate formats: room caption set, mini house profile, sentence repair.

### Lesson 55 — The Old House — Language Arts
Verified progression:
- Creative consolidation of unit language.
Engine behaviour:
- Suitable alternates: mini-book, room rhyme, simple house role-play.
- Avoid invented copyrighted text.

### Lesson 56 — The Old House — Listening
Verified progression:
- Review/extension cycle.
Engine behaviour:
- Listen for contrasting room/object details.
- Alternate formats: compare-two-rooms grid, listen-and-mark differences, object-location bingo.

### Lesson 57 — The Old House — Speaking
Verified progression:
- Review/extension speaking.
Engine behaviour:
- Require full simple sentence responses where appropriate.
- Alternate formats: spot-the-difference talk, house tour pairwork, question-card exchange.

### Lesson 58 — The Old House — Reading
Verified progression:
- Review/extension reading.
Engine behaviour:
- Reading should move beyond isolated words to simple detail retrieval.
- Alternate formats: room clue cards, true/false/correct, sentence-to-picture match.

### Lesson 59 — The Old House — Writing
Verified progression:
- Review/extension writing.
Engine behaviour:
- Produce short coherent room/house descriptions.
- Alternate formats: guided paragraph, room fact file, house brochure panel.
- Keep Year 2 sentence load appropriate.

### Lesson 60 — The Old House — Language Arts
Verified progression:
- End-of-cycle creative response.
Engine behaviour:
- Product/performance may combine speaking and simple writing.
- Must remain grounded in The Old House content.

## PRIMARY YEAR 2 ENGLISH — TRANSITION TO GET DRESSED! EXEMPLARS 61–70

### Lesson 61 — Get dressed! — Listening
Verified progression:
- New unit transition: clothing vocabulary and simple descriptions/instructions.
Engine behaviour:
- Listening should identify clothing items/details from verified source.
- Alternate formats: listen-and-point clothing cards, outfit grid, item selection.

### Lesson 62 — Get dressed! — Speaking
Verified progression:
- Speaking focus using clothing vocabulary.
Engine behaviour:
- Oral identification/description of clothing.
- Alternate formats: outfit talk, pair clothing quiz, describe-and-guess.

### Lesson 63 — Get dressed! — Reading
Verified progression:
- Reading simple clothing words/phrases/sentences.
Engine behaviour:
- Alternate formats: read-and-match clothing, label-to-picture match, clothing clue cards.

### Lesson 64 — Get dressed! — Writing
Verified progression:
- Writing simple clothing descriptions.
Engine behaviour:
- Alternate formats: outfit captions, label-and-write, guided sentence set.
- Check spelling and punctuation.

### Lesson 65 — Get dressed! — Language Arts
Verified progression:
- Creative response tied to clothing theme.
Engine behaviour:
- Suitable alternates: clothing rhyme, outfit mini-book, simple fashion role-play.
- Keep content age-appropriate and source-grounded.

### Lesson 66 — Get dressed! — Listening
Verified progression:
- Review/extension listening.
Engine behaviour:
- Listen for clothing detail/selection.
- Alternate formats: listen-and-dress character, detail grid, item sorting by heard clues.

### Lesson 67 — Get dressed! — Speaking
Verified progression:
- Review/extension speaking.
Engine behaviour:
- Pair/group talk around clothing choices/descriptions.
- Alternate formats: outfit interview, describe-and-find, information gap.

### Lesson 68 — Get dressed! — Reading
Verified progression:
- Review/extension reading.
Engine behaviour:
- Read simple clothing-related descriptions for detail.
- Alternate formats: clue-to-outfit match, true/false/correct, read-and-colour where source supports it.

### Lesson 69 — Get dressed! — Writing
Verified progression:
- Review/extension writing.
Engine behaviour:
- Produce simple outfit descriptions using verified language.
- Alternate formats: outfit profile card, picture-to-sentence, sentence repair.
- Avoid adding unverified garment vocabulary.

### Lesson 70 — Get dressed! — Language Arts
Verified progression:
- Creative consolidation before next cycle.
Engine behaviour:
- Performance/product can combine clothing vocabulary with speaking/writing.
- No invented copyrighted text.


## PRIMARY YEAR 2 ENGLISH — GET DRESSED! EXEMPLARS 71–80

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-check: Primary Year 2 SK Scheme of Work.

### Lesson 71 — Get dressed! — Listening
Verified SOW:
- Theme: World of Self, Family and Friends.
- Topic: Get dressed!
- Language focus: further practice of present continuous 3rd person singular statements/questions.
- Main: Listening 1.1.1 recognise/reproduce high-frequency target phonemes.
- Complementary: Reading 3.1.4 segment phonemes (CVC, CCVC, CVCV, CCV).

Engine behaviour:
- Listening/phoneme recognition is the evidence spine.
- Keep present continuous 3rd-person language explicit.
- Alternate formats: sound discrimination, listen-and-segment, picture + sound match.

### Lesson 72 — Get dressed! — Speaking
Verified progression:
- Continues present continuous and clothing context.
- Main skill: Speaking.

Engine behaviour:
- Oral question/answer and description should dominate.
- Alternate formats: what-is-he/she-wearing talk, action-picture prompts, pair describe-and-guess.
- Preserve 3rd-person singular forms.

### Lesson 73 — Get dressed! — Reading
Verified progression:
- Reading focus in same unit cycle.

Engine behaviour:
- Read simple clothing/action descriptions for specific detail.
- Alternate formats: sentence-picture match, read-and-identify person, true/false/correct.
- Do not invent textbook text.

### Lesson 74 — Get dressed! — Writing
Verified progression:
- Writing focus on simple present-continuous clothing descriptions.

Engine behaviour:
- Pupils produce short accurate sentences based on verified visuals/content.
- Alternate formats: outfit captions, sentence completion-to-free write, picture-to-sentence.
- Check spelling/punctuation and subject-verb form.

### Lesson 75 — Get dressed! — Language Arts
Verified progression:
- Language Arts tied to unit theme.

Engine behaviour:
- Creative response may use clothing/action language.
- Suitable alternates: chant/rap, mime-and-say, mini character card.
- No invented copyrighted text.

### Lesson 76 — Get dressed! — Listening
Verified progression:
- Review/extension listening.

Engine behaviour:
- Listen for clothing/material/action details.
- Alternate formats: listen-and-tick outfit grid, detail match, listen-and-place.

### Lesson 77 — Get dressed! — Speaking
Verified progression:
- Speaking review/extension.

Engine behaviour:
- Pair/group talk about clothing/materials or actions.
- Alternate formats: outfit interview, describe-and-find, information gap.
- Keep source vocabulary controlled.

### Lesson 78 — Get dressed! — Listening
Verified SOW:
- Language focus: recycled clothes vocabulary; materials vocabulary including cotton, wool, woollen, leather.
- Main: Listening 1.3.1 understand teacher/classmate message using visual clues.
- Complementary: Speaking 2.1.5 describe objects using suitable words/phrases.
- Textbook: Superminds 1 p.90.
- SOW note: use CD or read the short text aloud for Activity 1.
- Cross-curricular: Science and technology.

Engine behaviour:
- Listening to material/clothing descriptions is primary.
- Speaking follow-up describes clothing objects/materials.
- Alternate formats: material sorting, listen-and-identify garment/material, object description cards.

### Lesson 79 — Get dressed! — Writing
Verified SOW:
- Language focus: adjectives to describe materials.
- Main: Writing 4.3.2 spell familiar high-frequency words accurately.
- Complementary: Speaking 2.1.5 describe objects using suitable words/phrases.
- Textbook: Superminds 1 p.91.
- SOW note: pupils work on posters and discuss poster content in English.
- Cross-curricular: Science and technology; Creativity and Innovation.

Engine behaviour:
- Written poster content is primary evidence.
- Include peer talk about poster while writing.
- Alternate formats: materials poster, object-material fact card, label-and-describe panel.

### Lesson 80 — Get dressed! — Language Arts
Verified SOW:
- Main: Language Arts 5.3.1 respond imaginatively/intelligibly through simple short chants or raps / other imaginative responses.
- Complementary: Speaking 2.1.5 describe objects using suitable words/phrases.
- Review/extend p.88–91.
- SOW suggests using/creating a text describing a person, similar to Activity 3 p.89, with creative response through mime or dressing up/acting.
- Cross-curricular: Creativity and Innovation.

Engine behaviour:
- Creative response must use verified person/clothing description language.
- Suitable outputs: mime, dress-up acting, short original chant/rap, character description performance.
- Do not reproduce copyrighted textbook text.


## PRIMARY YEAR 2 ENGLISH — GET DRESSED! / THE ROBOT EXEMPLARS 81–100

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-check: Primary Year 2 SK Scheme of Work.

### Lesson 81 — Get dressed! — Listening
Verified progression:
- Continues Get dressed! review/extension.
Engine behaviour:
- Listen for clothing/material/person-description details.
- Alternate formats: listen-and-identify person, outfit detail grid, material match.

### Lesson 82 — Get dressed! — Speaking
Verified progression:
- Speaking review/extension using clothing/person descriptions.
Engine behaviour:
- Pair/group oral production should dominate.
- Alternate formats: describe-and-guess, outfit interview, character description carousel.

### Lesson 83 — Get dressed! — Reading
Verified progression:
- Reading simple person/clothing descriptions.
Engine behaviour:
- Read for specific detail and identify person/outfit.
- Alternate formats: clue-to-person match, true/false/correct, read-and-select.

### Lesson 84 — Get dressed! — Writing
Verified progression:
- Writing simple clothing/person descriptions.
Engine behaviour:
- Produce short linked sentences using verified vocabulary.
- Alternate formats: character profile, outfit caption set, sentence repair.

### Lesson 85 — Get dressed! — Language Arts
Verified progression:
- Creative consolidation of unit language.
Engine behaviour:
- Product/performance may include mime, role-play, mini chant/rap or character card.
- Do not reproduce copyrighted source text.

### Lesson 86 — Get dressed! — Listening
Verified progression:
- Further review of materials/clothing descriptors.
Engine behaviour:
- Listening detail retrieval must remain primary.
- Alternate formats: listen-and-sort materials, item/detail checklist, object description match.

### Lesson 87 — Get dressed! — Speaking
Verified progression:
- Speaking review/extension.
Engine behaviour:
- Encourage complete simple descriptive statements.
- Alternate formats: mystery outfit, partner questioning, describe-and-find.

### Lesson 88 — Get dressed! — Reading
Verified progression:
- Reading review/extension.
Engine behaviour:
- Use familiar unit vocabulary and sentence patterns.
- Alternate formats: read-and-draw, matching descriptions to characters, information hunt.

### Lesson 89 — Get dressed! — Writing
Verified progression:
- Writing review/extension.
Engine behaviour:
- Use known vocabulary to write a short coherent description.
- Alternate formats: mini poster, outfit fact file, guided paragraph.
- Keep Year 2 sentence load appropriate.

### Lesson 90 — Get dressed! — Language Arts
Verified progression:
- End-of-unit consolidation.
Engine behaviour:
- Creative response must recycle verified clothing/material language.
- Suitable outputs: performance, illustrated mini-book, simple role-play.

## TRANSITION — THE ROBOT

### Lesson 91 — The Robot — Listening
Verified progression:
- New unit transition into robot/body/action content.
- Main skill: Listening.
Engine behaviour:
- Listening should identify robot/body/action details from verified source.
- Alternate formats: listen-and-point body parts, action grid, robot instruction match.
- Do not invent exact vocabulary until page/task extraction.

### Lesson 92 — The Robot — Speaking
Verified progression:
- Speaking using robot/body/action language.
Engine behaviour:
- Oral commands/descriptions should dominate.
- Alternate formats: robot commander, describe-the-robot, action guessing.

### Lesson 93 — The Robot — Reading
Verified progression:
- Reading simple robot/body/action phrases or sentences.
Engine behaviour:
- Alternate formats: read-and-match parts, instruction-to-picture, clue cards.
- Exact textbook wording remains pending extraction.

### Lesson 94 — The Robot — Writing
Verified progression:
- Writing simple robot/body/action descriptions or instructions.
Engine behaviour:
- Alternate formats: robot labels + sentences, simple instruction list, picture-to-sentence.
- Check spelling/punctuation.

### Lesson 95 — The Robot — Language Arts
Verified progression:
- Creative response tied to robot theme.
Engine behaviour:
- Suitable alternates: robot chant, mime sequence, mini robot comic.
- No invented copyrighted source text.

### Lesson 96 — The Robot — Listening
Verified progression:
- Review/extension listening.
Engine behaviour:
- Listen for body/action/instruction details.
- Alternate formats: listen-and-build robot, detail grid, action sequence.

### Lesson 97 — The Robot — Speaking
Verified progression:
- Review/extension speaking.
Engine behaviour:
- Pair/group interaction around commands or robot description.
- Alternate formats: robot role-play, command chain, describe-and-draw.

### Lesson 98 — The Robot — Reading
Verified progression:
- Review/extension reading.
Engine behaviour:
- Read short instructions/descriptions for detail.
- Alternate formats: instruction ordering, clue-to-robot match, true/false/correct.

### Lesson 99 — The Robot — Writing
Verified progression:
- Review/extension writing.
Engine behaviour:
- Produce simple robot description/instruction text using verified language.
- Alternate formats: robot fact card, guided instruction set, caption panel.

### Lesson 100 — The Robot — Language Arts
Verified progression:
- Creative consolidation of robot unit language.
Engine behaviour:
- Product/performance may combine movement, speaking and simple writing.
- Keep all language tied to verified unit content.
- No invented copyrighted text.


## PRIMARY YEAR 2 ENGLISH — THE ROBOT EXEMPLARS 101–120

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-check: Primary Year 2 SK Scheme of Work / textbook unit progression.

### Lesson 101 — The Robot — Listening
Verified progression:
- Continues The Robot unit.
- Listening focus on body/action/instruction language.
Engine behaviour:
- Listen for specific details and commands.
- Alternate formats: listen-and-build robot, action/detail grid, command-to-picture match.

### Lesson 102 — The Robot — Speaking
Verified progression:
- Speaking focus using robot/body/action language.
Engine behaviour:
- Pair/group oral interaction should dominate.
- Alternate formats: robot commander, describe-and-draw, action guessing chain.

### Lesson 103 — The Robot — Reading
Verified progression:
- Reading simple robot descriptions/instructions.
Engine behaviour:
- Read for detail and sequence.
- Alternate formats: instruction ordering, clue-to-robot match, sentence-picture match.

### Lesson 104 — The Robot — Writing
Verified progression:
- Writing simple robot description/instruction text.
Engine behaviour:
- Alternate formats: robot fact card, guided instruction set, labelled robot + sentences.
- Check spelling/punctuation.

### Lesson 105 — The Robot — Language Arts
Verified progression:
- Creative consolidation of robot/body/action language.
Engine behaviour:
- Suitable alternates: robot chant, mime sequence, mini comic.
- No invented copyrighted text.

### Lesson 106 — The Robot — Listening
Verified progression:
- Review/extension listening.
Engine behaviour:
- Listen for differences in robot/body/action descriptions.
- Alternate formats: compare-two-robots, listen-and-mark, instruction bingo.

### Lesson 107 — The Robot — Speaking
Verified progression:
- Review/extension speaking.
Engine behaviour:
- Encourage complete simple oral descriptions/commands.
- Alternate formats: mystery robot, pair command challenge, robot interview.

### Lesson 108 — The Robot — Reading
Verified progression:
- Review/extension reading.
Engine behaviour:
- Use familiar verified unit language.
- Alternate formats: read-and-correct, clue hunt, true/false/correct.

### Lesson 109 — The Robot — Writing
Verified progression:
- Review/extension writing.
Engine behaviour:
- Produce a short coherent robot description/instruction sequence.
- Alternate formats: mini poster, fact file, guided paragraph.

### Lesson 110 — The Robot — Language Arts
Verified progression:
- Creative end-of-cycle response.
Engine behaviour:
- Performance/product may combine movement, speaking and simple writing.
- Keep content tied to The Robot.

### Lesson 111 — The Robot — Listening
Verified progression:
- Further consolidation/listening assessment within unit.
Engine behaviour:
- Target remaining comprehension gaps.
- Alternate formats: listening checklist, detail sort, command sequence.

### Lesson 112 — The Robot — Speaking
Verified progression:
- Further speaking consolidation.
Engine behaviour:
- Use structured pair/group interaction.
- Alternate formats: robot tour, command relay, describe-and-find.

### Lesson 113 — The Robot — Reading
Verified progression:
- Further reading consolidation.
Engine behaviour:
- Read for specific details from familiar source content.
- Alternate formats: information hunt, matching, sequencing.

### Lesson 114 — The Robot — Writing
Verified progression:
- Further writing consolidation.
Engine behaviour:
- Focus on accurate simple sentences.
- Alternate formats: caption strip, instruction card, description repair.

### Lesson 115 — The Robot — Language Arts
Verified progression:
- Language Arts consolidation.
Engine behaviour:
- Creative response may reuse known robot characters/actions.
- No invented source text.

### Lesson 116 — The Robot — Listening
Verified progression:
- Review/extension.
Engine behaviour:
- Use familiar unit language and target listening accuracy.
- Alternate formats: robot detail dictation, listen-and-draw, compare-and-check.

### Lesson 117 — The Robot — Speaking
Verified progression:
- Review/extension.
Engine behaviour:
- Encourage question/answer and descriptive speaking.
- Alternate formats: robot guessing game, peer interview, action prompt talk.

### Lesson 118 — The Robot — Reading
Verified progression:
- Review/extension.
Engine behaviour:
- Reading must require detail selection or sequencing.
- Alternate formats: clue-to-picture, sentence order, read-and-fix.

### Lesson 119 — The Robot — Writing
Verified progression:
- Review/extension.
Engine behaviour:
- Produce short guided text tied to verified unit content.
- Alternate formats: mini robot manual, short profile, caption set.

### Lesson 120 — The Robot — Language Arts
Verified progression:
- End-of-unit creative consolidation before next topic transition.
Engine behaviour:
- Product/performance may combine role-play, movement, simple writing.
- Keep content source-grounded.

## TRANSITION NOTE — YEAR 2
The next major unit after The Robot is **At the beach**. Do not merge robot/body/action language into the next unit's lesson mapping.


## PRIMARY YEAR 2 ENGLISH — THE ROBOT / AT THE BEACH EXEMPLARS 101–120

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-check: Primary Year 2 SK Scheme of Work.

### Lesson 101 — The Robot — Listening
Verified progression:
- Continues The Robot unit.
Engine behaviour:
- Listening for body/action/instruction details.
- Alternate formats: listen-and-build robot, action grid, sequence identification.

### Lesson 102 — The Robot — Speaking
Verified progression:
- Speaking review/extension.
Engine behaviour:
- Oral commands/descriptions remain central.
- Alternate formats: robot commander, describe-and-draw, partner instruction challenge.

### Lesson 103 — The Robot — Reading
Verified progression:
- Reading short robot/action instructions or descriptions.
Engine behaviour:
- Alternate formats: read-and-order, clue-to-robot match, true/false/correct.
- Keep source wording conservative until exact page extraction.

### Lesson 104 — The Robot — Writing
Verified progression:
- Writing simple robot descriptions/instructions.
Engine behaviour:
- Alternate formats: robot fact card, instruction list, caption panel.
- Check spelling/punctuation and command sequence.

### Lesson 105 — The Robot — Language Arts
Verified progression:
- Creative consolidation tied to robot theme.
Engine behaviour:
- Suitable alternates: robot chant, mime sequence, mini comic, role-play.
- No invented copyrighted source text.

### Lesson 106 — The Robot — Listening
Verified progression:
- Further review/extension listening.
Engine behaviour:
- Use formative gaps from preceding robot lessons.
- Alternate formats: listen-and-correct robot plan, detail checklist, action sequencing.

### Lesson 107 — The Robot — Speaking
Verified progression:
- Speaking review/extension.
Engine behaviour:
- Full simple responses and clear commands where appropriate.
- Alternate formats: command chain, describe-and-guess robot, pair information gap.

### Lesson 108 — The Robot — Reading
Verified progression:
- Reading review/extension.
Engine behaviour:
- Focus on specific detail and instruction meaning.
- Alternate formats: instruction hunt, sentence-to-picture match, sequencing cards.

### Lesson 109 — The Robot — Writing
Verified progression:
- Writing review/extension.
Engine behaviour:
- Produce short coherent robot description/instruction set.
- Alternate formats: guided paragraph, robot brochure card, error correction.

### Lesson 110 — The Robot — Language Arts
Verified progression:
- End-of-unit creative consolidation.
Engine behaviour:
- Product/performance may combine movement, speaking and simple writing.
- Keep content tied to verified robot/body/action language.

## TRANSITION — AT THE BEACH

### Lesson 111 — At the beach — Listening
Verified progression:
- New unit transition into beach/holiday-related vocabulary and simple descriptions.
Engine behaviour:
- Listening should identify beach items/people/actions from verified source.
- Alternate formats: listen-and-point scene, beach item grid, picture detail selection.
- Do not invent exact item list until source page extraction.

### Lesson 112 — At the beach — Speaking
Verified progression:
- Speaking focus using beach scene vocabulary.
Engine behaviour:
- Oral description/question-answer around beach scene.
- Alternate formats: describe-the-picture, beach scene interview, pair spot-and-say.

### Lesson 113 — At the beach — Reading
Verified progression:
- Reading simple beach-related words/phrases/sentences.
Engine behaviour:
- Alternate formats: read-and-match scene items, clue cards, sentence-picture match.

### Lesson 114 — At the beach — Writing
Verified progression:
- Writing simple beach scene descriptions.
Engine behaviour:
- Alternate formats: picture captions, mini scene profile, guided sentence set.
- Check spelling and punctuation.

### Lesson 115 — At the beach — Language Arts
Verified progression:
- Creative response tied to beach theme.
Engine behaviour:
- Suitable alternates: beach rhyme, mini-book, simple scene role-play.
- No invented copyrighted text.

### Lesson 116 — At the beach — Listening
Verified progression:
- Review/extension listening.
Engine behaviour:
- Listen for beach item/person/action details.
- Alternate formats: listen-and-mark scene, detail grid, sequence match.

### Lesson 117 — At the beach — Speaking
Verified progression:
- Review/extension speaking.
Engine behaviour:
- Pair/group talk around beach activities/scenes.
- Alternate formats: describe-and-find, beach interview, information gap.

### Lesson 118 — At the beach — Reading
Verified progression:
- Review/extension reading.
Engine behaviour:
- Read simple scene descriptions for detail.
- Alternate formats: clue-to-picture match, true/false/correct, information hunt.

### Lesson 119 — At the beach — Writing
Verified progression:
- Review/extension writing.
Engine behaviour:
- Produce short scene description using verified language.
- Alternate formats: beach postcard panel, scene caption set, guided mini paragraph.

### Lesson 120 — At the beach — Language Arts
Verified progression:
- Creative consolidation before next cycle.
Engine behaviour:
- Product/performance may combine beach vocabulary with speaking/writing.
- Keep output age-appropriate and source-grounded.


## PRIMARY YEAR 2 ENGLISH — AT THE BEACH EXEMPLARS 121–140

Source status: WEB_VERIFIED_PENDING_DRIVE_COPY
Primary cross-check: Primary Year 2 SK Scheme of Work.

### Lesson 121 — At the beach — Listening
Verified progression:
- Continues beach/holiday scene language.
Engine behaviour:
- Listen for scene/item/action details.
- Alternate formats: listen-and-mark beach picture, detail checklist, action grid.

### Lesson 122 — At the beach — Speaking
Verified progression:
- Speaking review/extension.
Engine behaviour:
- Pair/group talk around beach scene and activities.
- Alternate formats: describe-and-find, beach interview, picture information gap.

### Lesson 123 — At the beach — Reading
Verified progression:
- Reading short beach-related descriptions.
Engine behaviour:
- Read for specific detail.
- Alternate formats: clue-to-picture match, true/false/correct, information hunt.

### Lesson 124 — At the beach — Writing
Verified progression:
- Writing simple beach scene sentences.
Engine behaviour:
- Alternate formats: beach postcard panel, caption set, guided mini paragraph.
- Check spelling and punctuation.

### Lesson 125 — At the beach — Language Arts
Verified progression:
- Creative consolidation linked to beach theme.
Engine behaviour:
- Suitable alternates: beach rhyme, mini-book, role-play, illustrated story response.
- No invented copyrighted text.

### Lesson 126 — At the beach — Listening
Verified progression:
- Further listening review/extension.
Engine behaviour:
- Use formative gaps from preceding lessons.
- Alternate formats: listen-and-correct scene, detail grid, sequence identification.

### Lesson 127 — At the beach — Speaking
Verified progression:
- Speaking review/extension.
Engine behaviour:
- Encourage complete simple responses.
- Alternate formats: picture talk, beach activity survey, information gap.

### Lesson 128 — At the beach — Reading
Verified progression:
- Reading review/extension.
Engine behaviour:
- Focus on specific information from familiar scene language.
- Alternate formats: read-and-select, clue cards, sequencing.

### Lesson 129 — At the beach — Writing
Verified progression:
- Writing review/extension.
Engine behaviour:
- Produce short coherent scene description.
- Alternate formats: mini postcard, scene profile, error correction.
- Keep Year 2 sentence load appropriate.

### Lesson 130 — At the beach — Language Arts
Verified progression:
- Creative consolidation.
Engine behaviour:
- Product/performance may combine speaking, simple writing and visuals.
- Keep all content tied to verified beach language.

### Lesson 131 — At the beach — Listening
Verified progression:
- Final review cycle begins.
Engine behaviour:
- Listening for detail across familiar beach vocabulary/actions.
- Alternate formats: scene bingo, listen-and-order, detail checklist.

### Lesson 132 — At the beach — Speaking
Verified progression:
- Speaking review.
Engine behaviour:
- Oral description/questioning about familiar beach scenes.
- Alternate formats: describe-and-draw, pair questioning, picture carousel.

### Lesson 133 — At the beach — Reading
Verified progression:
- Reading review.
Engine behaviour:
- Read familiar sentences/short text for details.
- Alternate formats: information hunt, true/false/correct, picture matching.

### Lesson 134 — At the beach — Writing
Verified progression:
- Writing review.
Engine behaviour:
- Guided-to-independent beach scene sentences.
- Alternate formats: caption series, simple postcard, short description.

### Lesson 135 — At the beach — Language Arts
Verified progression:
- Creative response using familiar unit language.
Engine behaviour:
- Suitable outputs: mini performance, illustrated text, short chant/rap.
- No copyrighted source text reproduction.

### Lesson 136 — At the beach — Listening
Verified progression:
- Consolidation listening.
Engine behaviour:
- Focus on any remaining weak vocabulary/detail recognition.
- Alternate formats: diagnostic listening grid, correction task, scene matching.

### Lesson 137 — At the beach — Speaking
Verified progression:
- Consolidation speaking.
Engine behaviour:
- Recycle established question/answer and description patterns.
- Alternate formats: mini interview, picture prompt talk, pair challenge.

### Lesson 138 — At the beach — Reading
Verified progression:
- Consolidation reading.
Engine behaviour:
- Use familiar unit content for specific-detail reading.
- Alternate formats: clue hunt, sentence ordering, read-and-correct.

### Lesson 139 — At the beach — Writing
Verified progression:
- Consolidation writing.
Engine behaviour:
- Short final unit writing based on verified vocabulary.
- Alternate formats: beach memory card, short scene description, caption set.

### Lesson 140 — At the beach — Language Arts
Verified progression:
- Final creative consolidation before Year 2 revision block.
Engine behaviour:
- Use only verified At the beach language.
- Product/performance may combine visual, oral and short written elements.

## PRIMARY YEAR 2 ENGLISH — YEAR-END REVISION EXEMPLARS 141–160

### Lesson 141 — Revision — Listening
Verified progression:
- Year-end revision begins across Year 2 themes.
Engine behaviour:
- Recycle known vocabulary/structures from Free Time, The Old House, Get dressed!, The Robot, At the beach.
- Alternate formats: mixed-topic listening quiz, picture selection, listen-and-do.

### Lesson 142 — Revision — Speaking
Verified progression:
- Mixed-topic speaking review.
Engine behaviour:
- Pair/group oral retrieval from Year 2 themes.
- Alternate formats: revision carousel, question cards, describe-and-guess.

### Lesson 143 — Revision — Reading
Verified progression:
- Mixed-topic reading review.
Engine behaviour:
- Read familiar Year 2 words/sentences for detail.
- Alternate formats: mixed-topic clue match, board-game reading prompts, information hunt.

### Lesson 144 — Revision — Writing
Verified progression:
- Mixed-topic writing review.
Engine behaviour:
- Guided sentence production using familiar vocabulary.
- Alternate formats: picture-to-sentence, short profile, correction task.

### Lesson 145 — Revision — Language Arts
Verified progression:
- Creative mixed-theme revision.
Engine behaviour:
- Suitable outputs: mini-book, chant/rap, role-play, theme poster.
- Keep all language previously verified.

### Lesson 146 — Revision — Listening
Verified progression:
- Further mixed-topic listening consolidation.
Engine behaviour:
- Target gaps from formative evidence.
- Alternate formats: listening stations, mixed-topic grid, detail correction.

### Lesson 147 — Revision — Speaking
Verified progression:
- Further speaking consolidation.
Engine behaviour:
- Oral retrieval and interaction across multiple themes.
- Alternate formats: find-someone-who, revision interview, topic roulette.

### Lesson 148 — Revision — Reading
Verified progression:
- Further reading consolidation.
Engine behaviour:
- Use familiar text/language only.
- Alternate formats: read-and-sort by topic, clue cards, short comprehension.

### Lesson 149 — Revision — Writing
Verified progression:
- Further writing consolidation.
Engine behaviour:
- Simple connected writing using familiar Year 2 language.
- Alternate formats: mini report, picture sequence captions, profile card.

### Lesson 150 — Revision — Language Arts
Verified progression:
- Creative revision response.
Engine behaviour:
- Product/performance integrates previously learned language.
- No new unsupported grammar/vocabulary.

### Lesson 151 — Revision — Listening
Verified progression:
- Final revision cycle.
Engine behaviour:
- Mixed-topic listening challenge from Year 2 content.
- Alternate formats: noughts-and-crosses listening quiz, listen-and-identify topic, response cards.

### Lesson 152 — Revision — Speaking
Verified progression:
- Final speaking review.
Engine behaviour:
- Pupils ask/answer using familiar patterns.
- Alternate formats: class quiz, pair prompt cards, mini presentation.

### Lesson 153 — Revision — Reading
Verified progression:
- Final reading review.
Engine behaviour:
- Read familiar Year 2 prompts/instructions and respond.
- Alternate formats: revision board game, read-and-do, clue hunt.

### Lesson 154 — Revision — Writing
Verified progression:
- Final writing review.
Engine behaviour:
- Guided-to-independent simple sentence production.
- Alternate formats: true/false sentence set, picture captioning, short topic card.

### Lesson 155 — Revision — Language Arts
Verified progression:
- Creative preparation for final performance/product.
Engine behaviour:
- Pupils select familiar topic language and plan a simple response/performance.

### Lesson 156 — Revision — Listening
Verified progression:
- Final listening consolidation.
Engine behaviour:
- Familiar language only, diagnostic and confidence-building.
- Alternate formats: mixed-topic listening grid, listen-and-match, peer checking.

### Lesson 157 — Revision — Speaking
Verified progression:
- Final speaking consolidation.
Engine behaviour:
- Short personal/group responses across familiar themes.
- Alternate formats: mini interview, class survey, topic presentation.

### Lesson 158 — Revision — Writing
Verified progression:
- Final writing consolidation.
Engine behaviour:
- Produce a simple Year 2 review artifact from familiar vocabulary.
- Alternate formats: alphabet/topic poster, vocabulary mini-book, topic sentence set.

### Lesson 159 — Revision — Reading
Verified progression:
- Reuse learner-produced revision materials where appropriate.
Engine behaviour:
- Read/match/classify familiar Year 2 vocabulary/sentences.
- Alternate formats: peer poster matching, word-slip sorting, topic classification.

### Lesson 160 — Revision — Language Arts
Verified progression:
- Final Year 2 creative/performance lesson.
Engine behaviour:
- Rehearse and present a simple response using familiar Year 2 language.
- Suitable outputs: dialogue, chant/rap, mini role-play, illustrated presentation.
- No new unsupported content.

## YEAR 2 QA STATUS AFTER LESSON 160
- Seed-bank coverage now spans Lessons 1–160.
- Topic progression preserved: Introduction/Free Time -> The Old House -> Get dressed! -> The Robot -> At the beach -> Revision.
- Exact textbook page/task details are only treated as exact where directly cross-checked.
- Generic progression entries remain CONTENT_DETAIL_PENDING until source pages/SOW rows are extracted precisely.
- Do not promote pending entries to exact textbook-grounded READY status without page/source verification.


## YEAR 2 QA CORRECTION — VERIFIED UNIT BOUNDARIES & LATE-LESSON STRUCTURE

Primary cross-check: Primary Year 2 SK Scheme of Work and independent Year 2 RPH/SOW index.

### Correct unit boundaries
- Free Time: Lessons 1–30
- The Old House: Lessons 31–55
- Get dressed!: Lessons 56–87
- The Robot: Lessons 88–125
- At the beach: Lessons 126–160

These boundaries supersede any earlier approximate transition notes in this seed bank.

### Verified late-lesson corrections

#### Lesson 120 — The Robot — Language Arts
- Theme: World of Stories
- Topic: The Robot
- Main: Language Arts 5.1.1
- Complementary: Language Arts 5.1.2
- SOW suggests a variation of "Dem Bones" to review/extend vocabulary from p.103, with movement and a skeleton cut-and-reassemble activity.
- Do not reproduce copyrighted lyrics. Preserve only the pedagogical pattern and verified page/topic reference.

#### Lesson 121 — The Robot — Listening
- Theme: World of Stories
- Topic: The Robot
- Language/grammar: review or extension of recently introduced language and vocabulary.
- This is still The Robot, not At the beach.

#### Lesson 126 onward — At the beach
- The At the beach unit begins at Lesson 126.
- Earlier entries that placed At the beach at Lesson 111 are approximate and must not be treated as exact unit mapping.

#### Lesson 133 — At the beach — Reading
- Main: Reading 3.2.2 understand specific information/details of simple sentences.
- Review/extend pp.106–109.
- Suggested pattern: pictures of objects in different places (e.g. a fish in the sea), pupils read location questions and match to answers.
- Use this as a verified read-for-detail/location pattern; do not invent extra source text.

#### Lesson 151 — At the beach — Reading
- Theme: World of Knowledge
- Topic: At the beach
- Language/grammar: review of unit topics, vocabulary and language.
- Main: Reading 3.2.2.
- Complementary: Reading 3.2.4 use a picture dictionary to find/list/categorise words from Year 2 topics/themes.
- Textbook: Superminds 1 p.117.
- This confirms Lessons 151+ remain within At the beach / end-of-year unit review, not a separate generic revision unit.

#### Lesson 152 — At the beach — Writing
- Theme: World of Knowledge
- Topic: At the beach
- Language/grammar: review of unit topics, vocabulary and language; question forms.
- Keep Year 2 end-cycle writing grounded in the At the beach unit and reviewed Year 2 language.

#### Lesson 155 — At the beach — Language Arts
- SOW places Lesson 155 within the final At the beach/end-of-year sequence.
- Use creative review/performance grounded in Year 2 learned content.

### QA rule
Any Year 2 seed entry created from approximate topic progression before this correction must defer to these verified lesson boundaries. Runtime/database mapping should use the corrected ranges above. Exact lesson-level skill, page, and task data still requires row-by-row extraction before READY status.
