"""Read-only preflight for PJPK RPH integration. Run from repository root."""
import ast
import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    "pjpk_rpt_bridge_v2659",
    "pjpk_activity_planner_v2665",
    "pjpk_activity_adapter_v2666",
    "pjpk_rph_quality_v2672",
    "pjpk_rph_composer_v2669",
)

def check():
    report = {"modules": {}, "app": {}, "ready_for_live": False}
    for name in MODULES:
        path = ROOT / (name + ".py")
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            report["modules"][name] = "syntax_ok"
        except (OSError, SyntaxError, UnicodeError) as exc:
            report["modules"][name] = "error: " + str(exc)
    app = ROOT / "app.py"
    try:
        source = app.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(app))
        report["app"]["syntax"] = "ok"
        report["app"]["pjpk_mentions"] = source.count("pjpk")
        report["app"]["local_rph_definitions"] = sum(
            isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "_local_rph_text"
            for n in ast.walk(tree)
        )
        report["app"]["composer_referenced"] = "compose_verified_pjpk_rph" in source
        report["app"]["quality_refinement_referenced"] = "refine_verified_pjpk_rph" in source
    except (OSError, SyntaxError, UnicodeError) as exc:
        report["app"]["error"] = str(exc)
    # This preflight is intentionally not a live deployment or PDF validation.
    return report

if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False, indent=2))
