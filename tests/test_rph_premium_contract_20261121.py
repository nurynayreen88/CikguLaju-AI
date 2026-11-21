"""Permanent owner-approved premium RPH contract for current AND future subjects.

When adding a new native subject/alias, update the JSON register, its two
real renderer tests and the approval record. Never silently expand adapters.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

from web.rph_equal_width_20261121 import MAX_WIDTH, RATIOS
from web.rph_native_pdf_header_20261121 import (
    EXPECTED_BM, EXPECTED_EN, SPECIAL, premium_pdf_story,
)
from web.rph_reference_style_20261121 import PALETTES, REFERENCE, color_for_state

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs/rph_premium_contract_20261121.json"
STANDARD = ROOT / "docs/RPH_PREMIUM_STANDARD_20261121.md"
AGENTS = ROOT / "AGENTS.md"


def _register():
    return json.loads(REGISTER.read_text(encoding="utf-8"))


def _literal_tuple(path: Path, name: str, function_name=None):
    """Read the precise subjects tested in existing native Word/PDF QA."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = tree.body
    if function_name:
        fn = next(
            node for node in nodes
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == function_name
        )
        nodes = fn.body
    return tuple(next(
        ast.literal_eval(node.value)
        for node in nodes
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name
                for target in node.targets)
    ))


def test_owner_standard_is_mandatory_and_persisted_in_repository():
    m = _register()
    assert m["schema_version"] == 1
    assert m["owner_approved_date"] == "2026-11-21"
    assert m["status"] == "MANDATORY"
    assert m["tracked_issue"] == 1182
    assert m["policy_document"] == "docs/RPH_PREMIUM_STANDARD_20261121.md"
    policy = STANDARD.read_text(encoding="utf-8")
    agents = AGENTS.read_text(encoding="utf-8")
    for phrase in (
        "semua kotak utama", "kanan atas", "Word dan PDF", "Sains",
        "PPKI", "Bahasa Arab", "SK/SP", "A4", "LIVE DISAHKAN",
    ):
        assert phrase.casefold() in policy.casefold(), phrase
    assert "## Syarat format RPH PREMIUM" in agents
    assert "RPH_PREMIUM_STANDARD_20261121.md" in agents
    assert "tests/test_rph_premium_contract_20261121.py" in agents


def test_no_new_native_palette_can_appear_without_subject_registration():
    m = _register()
    canon = m["regular_native_ltr_subjects"]
    aliases = m["aliases"]
    exceptions = m["palette_special_cases"]
    assert len(canon) == len(set(canon)) == 9
    assert len(aliases) == len(set(aliases))
    assert not (set(canon) & set(aliases))
    assert set(aliases.values()) <= set(canon)
    # New palette keys MUST be accounted for by updating the approval
    # register. Do not silently apply the generic LTR style to an unknown
    # subject; a registered subject also needs both renderer regressions.
    approved = set(canon) | set(aliases) | set(exceptions)
    assert set(PALETTES) == approved, (
        "New/unregistered RPH subject color or missing approved subject",
        sorted(set(PALETTES) ^ approved),
    )
    for alias, subject in aliases.items():
        assert PALETTES[alias] == PALETTES[subject], (alias, subject)
    for subject in canon:
        assert color_for_state({"task": "rph", "subject": subject})
        assert color_for_state({"task": "rpt", "subject": subject}) is None


def test_every_registered_native_ltr_subject_is_in_word_and_pdf_regression():
    m = _register()
    allowed = set(m["regular_native_ltr_subjects"])
    pdf_tested = set(_literal_tuple(
        ROOT / "tests/test_rph_native_pdf_header_20261121.py",
        "SUBJECTS"))
    word_tested = set(_literal_tuple(
        ROOT / "tests/test_rph_premium_header_20261121.py",
        "names", "test_all_nine_legacy_subjects_keep_every_source_word_and_header_right"))
    assert {item.casefold() for item in pdf_tested} == allowed
    assert {item.casefold() for item in word_tested} == allowed


def test_special_renderers_remain_protected_not_generic_ltr():
    m = _register()
    markers = set(m["protected_special_markers"])
    assert markers == set(SPECIAL)
    assert set(REFERENCE) <= markers
    for s in (
        {"task": "rph", "subject": "Sains"},
        {"task": "rph", "subject": "Science"},
        {"task": "rph", "subject": "Matematik", "curriculum_version": "DLP"},
        {"task": "rph", "subject": "English", "programme": "PPKI"},
        {"task": "rph", "subject": "Bahasa Arab"},
    ):
        assert color_for_state(s) is None, s
    # PI/Jawi deliberately has a palette, but must not go through the
    # generic PDF LTR table reflow. Verified specialty tests cover real
    # seven-flowable fixture, not just this no-op smoke.
    assert "pendidikan islam" in m["palette_special_cases"]
    assert "pendidikan islam" in markers
    inert = ["original_special_rph"]
    for s in (
        {"task": "rph", "subject": "Pendidikan Islam"},
        {"task": "rph", "subject": "Bahasa Arab"},
        {"task": "rph", "subject": "Sains"},
    ):
        assert premium_pdf_story(s, inert) is inert


def test_existing_outer_widths_and_header_fields_are_explicitly_fixed():
    m = _register()
    layout = m["native_contract"]
    assert layout["word_table_count"] == len(RATIOS) == 4
    assert layout["word_max_table_width_twips"] == MAX_WIDTH == 10630
    assert sum(RATIOS[0]) == MAX_WIDTH
    assert layout["pdf_outer_table_width_mm"] == 172
    assert layout["pdf_story_flowables"] == 7
    assert len(layout["required_table_sections"]) == 4
    assert layout["pdf_teacher_fields_right"] == [
        "class", "date", "day", "time", "pupil_count",
    ]
    for labels in (EXPECTED_BM, EXPECTED_EN):
        assert len(labels) == 8
    assert EXPECTED_BM[5] == "Kelas"
    assert EXPECTED_EN[5] == "Class"
    assert "RTL" in layout["direction"]


def test_new_subject_acceptance_has_all_non_destructive_gates():
    m = _register()
    requirements = set(m["required_checks"])
    assert len(requirements) == len(m["required_checks"])
    assert len(requirements) >= 12
    for required in (
        "equal_left_and_right_outer_edges_on_every_main_box",
        "teacher_metadata_on_top_right_with_approved_rtl_exception",
        "blank_teacher_metadata_without_lines_or_placeholders",
        "word_pdf_content_and_visual_parity_per_generator",
        "verified_sk_sp_descriptions_and_curriculum_mappings",
        "protected_specialty_subject_and_script_layouts",
        "tested_per_subject_per_year_per_download_route",
        "no_user_quota_spend_for_qa_without_authorization",
        "render_live_and_real_download_confirmation_before_live_status",
    ):
        assert required in requirements
    routes = m["web_routes_requiring_individual_word_pdf_audit"]
    assert len(routes) == len(set(routes))
    assert "telegram-native-pdp-sequence" in routes
    assert "telegram-integrated-english-2027" in routes
    assert "PPKI/SJKC/SJKT dedicated clients" in routes
    assert "other future subjects" in m["future_or_separately_audited_programmes"]



def test_one_universal_rph_box_layout_and_only_two_rtl_subjects():
    """RTL changes reading order, never grants different RPH boxes or widths."""
    m = _register()
    layout = m["universal_layout"]
    assert layout["rule"] == "ONE_OUTER_BOX_LAYOUT_ALL_SUBJECTS"
    assert layout["all_subjects_same_box_design"] is True
    assert layout["all_subjects_equal_outer_box_width"] is True
    assert layout["exceptions_affect_direction_only"] is True
    assert layout["direction_default"] == "LTR"
    assert set(layout["rtl_only_subjects"]) == {
        "pendidikan islam", "bahasa arab",
    }
    assert "outer_box_geometry" in layout["rtl_does_not_change"]
    assert "overall_box_width" in layout["rtl_does_not_change"]
    assert "main_section_hierarchy" in layout["rtl_does_not_change"]
    assert layout["structural_sections"] == m["native_contract"]["required_table_sections"]
    assert set(layout["rtl_applies_to"]) == {
        "text_direction", "labels", "paragraph_alignment", "column_reading_order",
    }
    for name in m["regular_native_ltr_subjects"]:
        assert name not in layout["rtl_only_subjects"], name
    for marker in ("sains", "science", "ppki", "dlp"):
        assert marker not in layout["rtl_only_subjects"], marker
    assert "one_universal_rph_outer_box_layout_even_for_rtl_subjects" in m["required_checks"]
    assert "rtl_direction_only_pendidikan_islam_and_bahasa_arab" in m["required_checks"]
    standard = STANDARD.read_text(encoding="utf-8")
    agents = AGENTS.read_text(encoding="utf-8")
    for phrase in ("SATU REKA BENTUK KOTAK", "SATU-SATUNYA PERBEZAAN ARAH",
                   "bukan kebenaran menggunakan lebar"):
        assert phrase.casefold() in standard.casefold(), phrase
    assert "HANYA SATU reka bentuk kotak RPH" in agents
    assert "bukan pengecualian untuk bentuk atau lebar kotak" in agents
