"""Render-only fallback for non-Jawi glyphs in PI RPH raster paragraphs.

Preserves all Arabic/Jawi codepoints and original DB/source text. Only the
per-paragraph raster copy is normalized when the chosen font lacks a glyph.
"""
import unicodedata

SAFE_REPLACEMENTS = {
    "\u200b": "", "\u200c": "", "\u200d": "", "\ufeff": "",
    "\ufe0e": "", "\ufe0f": "",
    "\u2022": "-", "\u25cf": "-", "\u25e6": "-",
    "\u25a0": "-", "\u25aa": "-", "\u25ab": "-",
    "\u2610": "[ ]", "\u2611": "[x]", "\u2612": "[x]",
    "\u2713": "OK", "\u2714": "OK", "\u2717": "X",
    "\u2705": "OK", "\u274c": "X", "\u2b50": "*",
    "\u2013": "-", "\u2014": "-", "\u2018": "'",
    "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2026": "...", "\u00a0": " ", "\u202f": " ",
    "\u2192": "->", "\u2190": "<-", "\u2194": "<->",
    "\u25a1": "[ ]", "\u25fb": "[ ]", "\u25fc": "[x]",
    "\u23f0": "Masa", "\u23f1": "Masa", "\u23f3": "Masa",
    "\U0001f4da": "Buku", "\U0001f4d6": "Buku",
    "\U0001f4dd": "Nota", "\U0001f4cb": "Senarai",
    "\U0001f3af": "Objektif", "\U0001f4a1": "Idea",
    "\U0001f464": "Murid", "\U0001f465": "Murid",
}
def sanitize_raster_text(text, font_path, cmap_fn):
    """Return (render_text, replaced codepoints); never change Jawi letters."""
    original = str(text or "")
    cmap = cmap_fn(font_path)
    output, changed = [], set()
    for ch in original:
        cp = ord(ch)
        if ch in "\n\r\t" or cp in cmap:
            output.append(ch)
            continue
        if 0x0600 <= cp <= 0x08FF:
            # Arabic/Jawi must never be silently substituted.
            output.append(ch)
            continue
        repl = SAFE_REPLACEMENTS.get(ch)
        if repl is None:
            decomposed = unicodedata.normalize("NFKD", ch)
            repl = "".join(c for c in decomposed if ord(c) in cmap)
            if not repl:
                category = unicodedata.category(ch)
                repl = "" if category in ("Cf", "Mn", "Me") else "?"
        # Replacements must themselves be representable by the active font.
        repl = "".join(c if ord(c) in cmap or c.isspace() else "?" for c in repl)
        output.append(repl)
        changed.add(cp)
    return "".join(output), sorted(changed)
