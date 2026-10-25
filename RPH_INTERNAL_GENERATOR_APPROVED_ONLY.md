# RPH publishing contract: internal generator, approved lessons only

## Roles
- **Developer/admin:** run the existing RPH generator offline against previously audited DSKP/RPT/SOW/textbook/Teacher's Book data; inspect each resulting lesson; revise; approve; publish an immutable versioned lesson record.
- **Teacher/user:** select year/form, subject and lesson/PdP; receive only the approved, pre-generated standalone lesson record rendered as an A4 PDF. The user-facing path must never generate or invent pedagogical content.

## Approval and delivery requirements
1. Resolve a stable key (year/form, subject, lesson/PdP), then select a record explicitly marked `approved` with source references and a version.
2. Reject missing, draft, or review-needed records with a clear not-yet-available message; never fall back to the AI or a generic template for curriculum content.
3. Personalize administrative fields (teacher, class, date, duration) only; preserve SK/SP, learning objectives, success criteria, activities, materials and assessment verbatim.
4. Render the approved content through the existing A4 PDF layout engine.
5. Audit changes before publishing a new version; retain previous approved versions for traceability.
6. Preserve legacy databases and code paths during migration. Do not enable the user-facing approval gate until the lookup, permissions and regression tests are complete.

## Current implementation status
This document is a required design contract, **not** a claim that the runtime already enforces approved-only RPH delivery. The English Year 1 lesson records currently in this branch remain drafts.
