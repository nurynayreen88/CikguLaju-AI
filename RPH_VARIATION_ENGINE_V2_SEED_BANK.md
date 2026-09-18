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
