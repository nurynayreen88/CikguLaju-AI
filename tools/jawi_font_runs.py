"""Plan font runs for mixed Jawi/Rumi text without altering source characters.

This module is deliberately independent of app startup and the database.
Rendering must retain logical text order and use RAQM for Arabic shaping.
"""
from functools import lru_cache

@lru_cache(maxsize=32)
def font_codepoints(path):
    from fontTools.ttLib import TTFont
    font = TTFont(path, lazy=True)
    try:
        return frozenset().union(*(set(t.cmap) for t in font["cmap"].tables))
    finally:
        font.close()

def select_runs(text, font_paths, maps=None):
    """Return (font path, exact substring) runs; fail rather than draw tofu."""
    if not font_paths:
        raise ValueError("No fonts supplied")
    maps = maps if maps is not None else [font_codepoints(p) for p in font_paths]
    if len(maps) != len(font_paths):
        raise ValueError("Font coverage count mismatch")
    runs = []
    for char in text:
        # Whitespace belongs to current run and never forces a font switch.
        if char.isspace() and runs:
            runs[-1] = (runs[-1][0], runs[-1][1] + char)
            continue
        choice = next((i for i, cmap in enumerate(maps) if ord(char) in cmap), None)
        if choice is None:
            raise ValueError(f"No font covers U+{ord(char):04X}")
        path = font_paths[choice]
        if runs and runs[-1][0] == path:
            runs[-1] = (path, runs[-1][1] + char)
        else:
            runs.append((path, char))
    return runs
