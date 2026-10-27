# Pendidikan Islam — Standalone RPH release gates

This is a staging-only checklist, not a claim that any RPH is approved.

1. **Source identity:** retain the existing Year / PdP / SK / SP sequence from the
   verified project DB or RPT. Never synthesize curriculum identifiers.
2. **Content:** each RPH must include lesson-specific objectives, teacher and
   pupil actions, sequential activities, PBD and an appropriate conclusion.
3. **Jawi:** keep original Unicode codepoints; no silent character substitution.
   Render through the *full current production class chain*, not only the base
   and last overrides. A partial-chain PDF is not production evidence.
4. **Visual:** inspect the generated A4 PDF for shaping, clipping, line spacing
   and readability. Do not shrink text simply to force a single page.
5. **Approval:** add to the standalone manifest as `approved` only after
   source comparison and visual inspection; record PDF SHA-256.
6. **Delivery:** never route users to an unapproved or missing PDF. Preserve
   existing bot generation as fallback until a verified bank exists.
7. **Safety:** no database reset, no automatic merge to `main`, no live
   Telegram token or webhook in test services.

Current status: sample PDF rendering was demonstrated with a partial class
chain; the complete live renderer and a DB-backed Pendidikan Islam RPH are
**not yet validated**.
