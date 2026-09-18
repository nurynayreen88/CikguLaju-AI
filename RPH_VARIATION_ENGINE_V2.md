# RPH Variation Engine v2 — CikguLaju AI

Status: DESIGN LOCK / implementation reference

## Purpose
Upgrade RPH generation from generic templates to lesson-specific, curriculum-locked variations.

## Source hierarchy
1. DSKP / RPT / SOW verified data = curriculum source of truth.
2. Textbook / workbook references = lesson-content and task-pattern context.
3. Teacher-created free lesson-plan examples (e.g. materials supplied by user, TeacherFiera-style references) = pedagogical pattern benchmark only.
4. Transition/remedial modules = optional activity-pattern bank for low-readiness, remediation, confidence-building and warm-up.

Never copy third-party lesson plans wholesale. Extract activity patterns, sequencing ideas and pedagogical structures, then generate original CikguLaju wording and combinations.

## Core pipeline
Lesson verified
→ Main Skill / Complementary Skill
→ exact SK/SP lock
→ Language/Content Focus
→ measurable objective
→ success criteria
→ Pre-Lesson
→ Guided Input
→ Controlled Practice
→ Pair/Group Application
→ Production / Task
→ Assessment / PBD evidence
→ Post-Lesson
→ Reflection

## Activity families
PRE_WARMUP
GUIDED_INPUT
PHONICS_SOUND_ACTION
LISTEN_IDENTIFY
LISTEN_MIME
PICTURE_MATCH
WORD_MATCH
CHANT_SONG
GUIDED_READING
GUIDED_WRITING
PAIR_DIALOGUE
PAIR_CHECK
ROLE_PLAY
INFORMATION_GAP
SORT_CLASSIFY
PICTURE_DICTIONARY
TEXTBOOK_TASK
PROJECT_POSTER
GAME
MOVEMENT_TPR
GROUP_TASK
MINI_PRESENTATION
WORKSHEET
PBD_CHECK
POST_RECAP
POST_GAME
POST_REFLECTION
REMEDIAL_FOUNDATION
ENRICHMENT_EXTENSION

## Required tags for each activity variant
subject
level/year/form
main_skill
complementary_skill
focus_type
activity_family
difficulty: remedial|core|extension
estimated_minutes
class_size_min
class_size_max
grouping: whole_class|pair|group|individual
materials_required
textbook_dependency
movement_level
reading_load
writing_load
assessment_evidence
suitable_for_multi_session
source_pattern
originality_status

## Selection rules
- Never select an activity only because the title/topic matches.
- SK/SP + skill/focus suitability must pass first.
- Prefer activities compatible with lesson duration and class size.
- Avoid repeating the same activity family in consecutive RPH for the same teacher/class when alternatives exist.
- Variation means different pedagogical route, not paraphrasing the same steps.
- If no suitable activity variant exists, fall back to a conservative verified pattern rather than invent curriculum content.

## Multi-session lesson rule
If the same lesson block appears multiple times in RPT/SOW with the same SK/SP, keep one lesson choice in UI but retain the actual session count internally.

For 2-session blocks:
Session 1: activate prior knowledge → model/input → guided/controlled practice.
Session 2: retrieve/review → application/production → assessment → reflection.

Do not deduplicate away legitimate repeated sessions.

## Patterns learned from supplied Year 1/phonics examples
- listen to target sounds → perform actions → identify target sounds → circle/match pictures → song/chant
- teacher model/mime → pupils imitate → pair practice → class check
- textbook page task → pair comparison → teacher check
- pair role play after modelling
- picture dictionary / list / categorise vocabulary
- poster/project creation followed by oral description
- post-lesson game, chant, matching, wordsearch or pair task
- reflection based on number of pupils achieving objectives / needing guidance

These are activity PATTERNS only, not copied lesson-plan text.

## Transition/remedial patterns
Use supplied transition modules as pedagogical inspiration for:
- low-readiness
- confidence-building
- foundational literacy
- warm-up
- remedial
- gradual release
These modules must not override official SK/SP or verified lesson sequencing.

## Objective generation
Objectives must be measurable and derived from verified SP, lesson focus and activity.
Prefer observable verbs such as identify, match, respond, describe, read, write, classify, produce, present, demonstrate.
Avoid generic objectives such as "understand the topic" when a measurable outcome is available.

## Success criteria
Success criteria should state observable evidence, e.g. target number/quality of responses, items matched, sentences produced, sounds recognised, information communicated, or task completed.
Do not invent numerical thresholds unless defined by source or a configurable teacher preference.

## PBD / assessment
Assessment must attach to the task that provides evidence.
Examples: observation checklist, oral response, pair performance, completed matching, worksheet item, short written product, mini presentation, exit response.
Avoid generic "teacher assesses pupils" without evidence.

## BBM coupling
BBM should be selected from activity requirements.
Examples:
picture cards, word cards, textbook, audio, mini whiteboard, worksheet, poster paper, scissors/glue, manipulatives.
Do not suggest BBM unrelated to the actual activity sequence.

## Variation identity
Store a route signature:
pre_family + guided_family + practice_family + application_family + assessment_family + post_family
Use this signature to reduce repeated RPH combinations.

## Copyright / provenance
Store source_pattern as provenance category only, for example:
USER_SUPPLIED_RPH_PATTERN
USER_SUPPLIED_PHONICS_PATTERN
USER_SUPPLIED_TRANSITION_PATTERN
TEACHERFIERA_STYLE_BENCHMARK
OFFICIAL_SOW_PATTERN
Do not store copied third-party paragraphs as runtime templates.


## RPH CONTENT WRITING LOCK — TEXTBOOK / ACTIVITY BOOK MUST APPEAR IN THE RPH CONTENT

The final RPH content itself must contain explicit teaching steps that use the verified textbook and, where available, the verified activity book. It is not enough for the engine to use these sources silently in the background.

### Required textbook references inside RPH content
When a verified textbook mapping exists, the lesson-plan content should naturally include instructions such as:
- Teacher directs pupils to the verified textbook page(s) for the selected Lesson.
- Pupils observe/read/listen/respond to the specific verified content on those page(s).
- Teacher elicits or models the lesson-linked vocabulary/language/skill from the textbook content.
- Pupils complete or discuss the relevant textbook task.
- Teacher checks responses and uses the textbook task as a bridge to the next activity.

Do not fabricate page numbers or textbook content. Only include page references/content already verified in mapping.

### Required activity-book references inside RPH content
When a verified activity-book/workbook mapping exists, the RPH should include an explicit follow-up instruction linked to it, for example:
- Teacher directs pupils to the verified activity-book page related to the Lesson.
- Pupils complete the relevant workbook practice as reinforcement.
- Teacher reviews selected responses/errors.
- CikguLaju then provides an ORIGINAL follow-up exercise using the same language/skill target but a different response format.

The RPH must distinguish:
1. **Book activity** — use the existing verified textbook/activity-book task.
2. **CikguLaju variation** — an original alternate-format activity to reinforce or assess the same learning target.

### Example sequencing pattern
PRE-LESSON
→ activate prior knowledge connected to textbook lesson content

LESSON DELIVERY 1
→ open verified textbook page
→ observe/listen/read the actual lesson content
→ teacher models / elicits target language or concept

LESSON DELIVERY 2
→ pupils complete the relevant textbook task
→ pair/group comparison or teacher check

LESSON DELIVERY 3
→ if activity book exists, use verified related activity-book exercise
→ review common responses/errors

LESSON DELIVERY 4
→ CikguLaju original alternate-format task using the same lesson content

ASSESSMENT
→ collect evidence from textbook/workbook task and/or the original CikguLaju task

POST-LESSON
→ short recap / retrieval / exit activity tied to the same content

### Output wording rule
Use direct, practical teacher-facing wording in the generated RPH. Avoid vague sentences such as:
- "Teacher conducts an activity based on the textbook."
- "Pupils do exercises in the activity book."

Prefer concrete wording grounded in verified mappings, e.g.:
- "Teacher asks pupils to refer to the mapped textbook page for this Lesson and identify the target words shown in the pictures."
- "Pupils complete the linked activity-book exercise, then compare answers in pairs."
- "Teacher follows with a CikguLaju picture-sorting task that practises the same target vocabulary in a different format."

When exact verified page/content metadata is available, include it. When it is not available, do not imply that it is known.

### RPH quality gate
A generated RPH should fail the quality gate if a verified textbook/activity-book mapping exists but:
- the book is not mentioned in the teaching steps,
- the mapped content is not used in the activity sequence,
- the original CikguLaju exercise is unrelated to the mapped book content,
- the generated exercise simply duplicates the activity-book exercise format.

## Safety checks before release
- exact SK/SP relation preserved
- no SP forcibly attached to first SK when a lesson has multiple SK
- lesson/session count preserved
- no fabricated curriculum facts
- activity sequence matches skill/focus
- no duplicate generic step blocks
- variation route differs meaningfully


## TEXTBOOK + ACTIVITY BOOK GROUNDING LOCK

### Mandatory source order for lesson-plan generation
For any verified Lesson, runtime generation must resolve sources in this order:
1. Verified RPT/SOW/DSKP -> Lesson identity, SK/SP, skill/focus.
2. Verified textbook mapping -> exact pages/content/tasks for that Lesson.
3. Verified activity-book mapping, when an activity book exists -> practice focus and difficulty reference.
4. RPH Variation Engine -> choose original teaching route around the verified content.

If textbook/activity-book mapping is unavailable or unverified, the engine must not invent page content, dialogue, vocabulary, task instructions, exercise type or answer content.

### Textbook grounding
The RPH must explicitly reflect the lesson-linked textbook content where available:
- vocabulary / language items,
- reading/listening/speaking/writing content,
- grammar or phonics focus,
- illustrations / situations / text type,
- task purpose and sequence,
- page-linked practice.

Variation is allowed only around the same verified lesson content. Example: add prediction, modelling, pair-check, retrieval, role-play, mini-whiteboard, exit-ticket or extension tasks without changing the curriculum focus.

### Activity-book grounding
When a verified activity book/workbook exists for the Lesson:
- use its topic, skill, language focus and expected pupil response as a reference;
- do NOT simply reproduce or lightly paraphrase its exercise;
- generated practice must test/reinforce the same lesson content using a DIFFERENT format.

Examples of valid format transformation:
- activity book matching -> generated sorting/classification;
- fill-in-the-blank -> generated picture prompt + short response;
- multiple choice -> generated mini-whiteboard / oral choice with justification;
- copying words -> generated label-the-picture / word-building;
- sentence completion -> generated guided dialogue / rearrange-and-write;
- textbook dialogue -> generated role-play cards;
- reading comprehension -> generated sequencing / true-false-correct / information hunt;
- workbook word search -> generated category game / card sort;
- tracing/phonics drill -> generated sound-action / picture discrimination / blending cards.

The semantic target stays the same; the response format changes.

### Generated worksheet rule
Every generated worksheet must record internally:
- linked rpt_entry_id,
- textbook page/content reference when verified,
- activity-book page/content reference when verified,
- target SK/SP,
- main/complementary skill,
- lesson focus,
- exercise_format,
- source_format_reference,
- transformation_type.

The generated exercise must be original in wording/layout and must not copy third-party workbook pages.

### Exercise-format diversity
Avoid giving the same exercise format repeatedly for the same Lesson/class.
Preferred rotating formats include:
PICTURE_MATCH
SORT_CLASSIFY
LABEL
SEQUENCE
INFORMATION_HUNT
TRUE_FALSE_CORRECT
GUIDED_DIALOGUE
ROLE_PLAY_CARD
WORD_BUILD
MINI_WHITEBOARD
SHORT_RESPONSE
PICTURE_PROMPT
ODD_ONE_OUT
CATEGORISE
REORDER
ERROR_CORRECTION
EXIT_TICKET
APPLICATION_TASK

### Two-session Lesson behaviour
For repeated RPT sessions with the same Lesson/SK/SP:
- Session 1: textbook-led input and guided practice.
- Session 2: activity-book-linked reinforcement and/or original alternate-format practice, then PBD evidence.
If no activity book exists, Session 2 uses an original extension/application task grounded in the textbook content.

### Release gate
A generated RPH/worksheet is not considered high-confidence unless:
- Lesson and SK/SP are verified,
- textbook mapping is verified when textbook exists,
- activity-book mapping is verified when workbook exists,
- generated exercise format is not a copy of the activity-book format,
- all generated content still assesses/reinforces the same Lesson focus.


## LESSON CONTENT PACK — CONTENT-FIRST RPH GENERATION

Before generating an RPH, build a Lesson Content Pack from verified sources.

Required fields:
- rpt_entry_id
- year/form
- subject
- unit/topic
- lesson_no / lesson_range
- session_count
- main_skill
- complementary_skill
- exact SK/SP relations
- language_or_content_focus
- textbook_title
- textbook_page_start
- textbook_page_end
- textbook_content_summary
- textbook_target_vocabulary
- textbook_target_language_or_concept
- textbook_text_type_or_visual_context
- textbook_task_type
- textbook_task_sequence
- teacher_book_reference if verified
- activity_book_title
- activity_book_page_start
- activity_book_page_end
- activity_book_content_summary
- activity_book_task_type
- activity_book_expected_response
- differentiation_hint
- assessment_evidence_hint
- mapping_status / provenance

### Generation rule
No RPH should be generated from Lesson number + SK/SP alone when a verified textbook mapping exists. The Lesson Content Pack must be loaded first and the teaching steps must be written around the actual mapped content.

### Year 1 English SOW grounding
For Primary Year 1 English, the verified SOW explicitly distinguishes textbook-based and non-textbook-based lessons. From Lesson 6 onward, textbook-based lessons use Superminds 1, while non-textbook-based lessons recycle and consolidate language/skills. Therefore:
- textbook-based lesson -> use mapped Superminds 1 content/task as the main lesson spine;
- non-textbook-based lesson -> use the SOW learning outline and previously learned textbook language as consolidation/recycling context;
- do not force a textbook page into a non-textbook-based lesson unless a verified mapping supports it.

### Concrete RPH-writing template
PRE-LESSON
- activate specific vocabulary/language/concept from the Lesson Content Pack;
- use one suitable retrieval/prediction/phonics/visual task.

LESSON DELIVERY A — SOURCE CONTENT
- direct pupils to the verified textbook page(s) or verified SOW outline;
- state what pupils look at/listen to/read/say/do from the mapped content;
- model/elicit the exact target language/concept.

LESSON DELIVERY B — SOURCE TASK
- pupils complete/discuss the actual mapped textbook task;
- include pair-check/group-check/teacher feedback where appropriate.

LESSON DELIVERY C — ACTIVITY BOOK, IF PRESENT
- direct pupils to the mapped activity-book page;
- state the skill/content reinforced;
- use the existing book task as reinforcement, not as the only evidence.

LESSON DELIVERY D — CIKGULAJU ORIGINAL VARIATION
- generate a different-format task using the same vocabulary/language/concept;
- vary pedagogy, response mode and grouping;
- do not copy the activity-book format.

ASSESSMENT / PBD
- specify the observable product/response from the source task and/or CikguLaju variation.

POST-LESSON
- retrieve, apply or reflect on the same mapped content.

### Quality rejection rules
Reject or downgrade an RPH if:
- it says only "refer to textbook" without using actual verified content;
- it mentions a workbook generically without verified mapping;
- generated activities could apply to almost any lesson;
- vocabulary/language/content in activities is not traceable to the Lesson Content Pack;
- source task and CikguLaju task have effectively the same format;
- textbook/activity-book content is invented when mapping is absent.

### Activity-book absent case
If no verified activity book exists:
- do not write "activity book" into the RPH;
- generate an original reinforcement/application task grounded in textbook/SOW content instead.
