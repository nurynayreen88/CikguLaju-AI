# Jawi production acceptance — blocked until real PDF evidence

This checklist is a release gate, not an approval.

- [ ] Load verified Pendidikan Islam SK/SP and lesson content from the existing database in read-only mode. Never invent curriculum values.
- [ ] Generate the RPH through the real application PDF entrypoint, not extracted AST classes or substitute helpers.
- [ ] Preserve original Unicode Jawi text; compare source codepoints before rendering.
- [ ] Save PDF, SHA-256, exact lesson identity and the renderer revision.
- [ ] Rasterize at print resolution and visually inspect joining, RTL order, diacritics, line wrapping and clipping.
- [ ] Confirm A4 portrait, one page, legible print size and no cut-off text.
- [ ] Compare a bot-delivered PDF with the test output; do not infer equivalence from synthetic smoke tests.
- [ ] Run py_compile, Jawi regression tests and read-only PRAGMA integrity_check for the database actually used.
- [ ] Record reviewer approval before marking any standalone RPH approved.

The existing synthetic 12-class v26.39 PDF only passes a smoke/layout test. No production PDF is approved. Do not merge or deploy this PR on the basis of this checklist.
