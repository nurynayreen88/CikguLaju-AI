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

## Safety checks before release
- exact SK/SP relation preserved
- no SP forcibly attached to first SK when a lesson has multiple SK
- lesson/session count preserved
- no fabricated curriculum facts
- activity sequence matches skill/focus
- no duplicate generic step blocks
- variation route differs meaningfully
