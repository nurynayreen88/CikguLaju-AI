"""One-Lesson Word A4 repair: English Year 4 Lesson 002 only.

Offline AST-locked Word-to-PDF audit found Year4 L002 2 pages and the
other 148 fixed-standard Year4 lessons 1 page in their existing layout.
Use the same text-preserving compact routine for that one fixed Lesson.
No change to Lesson content, source files, native PDF, DB or quotas.
"""
from web.english_y4_standalone_runtime import _selected_y4_lesson, load_release_candidate
from web.english_y6_word_a4_runtime import compact_word_file


def _target(state):
    if not isinstance(state, dict):
        return False
    if str(state.get("task") or "").strip().casefold() != "rph":
        return False
    if _selected_y4_lesson(state) != 2:
        return False
    lesson = load_release_candidate(2)
    if lesson is None:
        return False
    sow = lesson["sow"]
    for field, code in (("sp_code",sow["main_ls"]),
                        ("bi_main_sp_code",sow["main_ls"]),
                        ("comp_sp_code",sow["complementary_ls"]),
                        ("bi_comp_sp_code",sow["complementary_ls"])):
        selected = str(state.get(field) or "").strip()
        if selected and selected != code:
            return False
    return True


def install(runtime):
    if getattr(runtime,"CIKGULAJU_ENGLISH_Y4_L002_WORD_A4_ACTIVE",False):
        return True
    old = getattr(runtime,"create_word_file",None)
    if not callable(old):
        return False

    def year4_l002_word(state,*args,**kwargs):
        path=old(state,*args,**kwargs)
        if _target(state):
            compact_word_file(path)
        return path

    runtime.create_word_file=year4_l002_word
    runtime.CIKGULAJU_ENGLISH_Y4_L002_WORD_A4_ACTIVE=True
    return True
