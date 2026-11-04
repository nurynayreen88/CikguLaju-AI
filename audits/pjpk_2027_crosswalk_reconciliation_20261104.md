# PJPK 2027: audit reconciliation (2026-11-04)

Status: STAGING; not READY. No production or database changes.

Source references:
- PJ Year 2 RPT: https://docs.google.com/document/d/1nOnaS3O9IBk-ZNcDGRUBtU8k2FCUnOGh1m8WU0ZgSDs/edit — 37 existing lessons plus four provisional aquatics entries, not 41 approved lessons.
- PJ Years 4–6 master: https://docs.google.com/document/d/1aVtES4Os11rDfCOwb2ZygtvLo0w48Hx07jP1ntkiUjw/edit
- PJ Years 4–6 standards index: https://docs.google.com/document/d/1DjQSztYXVGUes94T0xt3EEMCkAeDNrGXq6-SBzfvsdU/edit
- PJ Year 6 master: https://docs.google.com/document/d/1z0mzea_DMr4amMFSwHvmp6sYuJzyNDAWnNkEEgHkGbg/edit

Findings:
1. Year 4 lessons 003–004 have candidate standard codes in index v54 but were unresolved in the earlier master. Verify against year-specific DSKP before release.
2. Year 5 has 33 indexed lessons; repeated standards in adjacent sessions need distinct learning objectives.
3. Year 6 restored lessons 003, 004 and 020 appear in appendices. Reconcile in place without duplicating lessons; check missing Unit 7 coverage.
4. Year 2 aquatics lessons require safety and facilities review; do not renumber 37 existing lessons until approved.
5. Review both PJ and PK independently for Years 1–6. The legacy 170 SP and 128 SK review rows are not a new audit count.

Release gate: exact DSKP evidence, textbook pages, RPH formative assessment, curriculum sequence, timetable/calendar mapping, DB integrity, and staging end-to-end tests. Never infer verified status from a candidate index.
