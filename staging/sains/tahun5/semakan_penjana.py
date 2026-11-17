"""Exact 2027 Year 5 SK Science source for the private RPH download service."""

import tempfile
from pathlib import Path

from dlp_year2_rph import _pdf, _word
from staging.sains.tahun5.eksport_2027 import build_source, render_rph
from tools.sains_y5_kssr2017_official_sp_statements_20261107 import checked_statements
from web.sains_unit_awal import PROCESS


class ReviewRuntime:
    """Serve the 2027 sequence independently of legacy Science identifiers."""

    CIKGULAJU_DB_V2600_ACTIVE = True  # build_source validates the independent RPT and DSKP source.

    def __init__(self):
        _, plans = build_source()
        statements = checked_statements()
        self.plans = {}
        self.catalog = []
        for number, plan in plans.items():
            code = f"SK27-SCI-Y5-PDP-{number:03d}"
            standard = ({"sk_title": "Kemahiran Proses Sains", "sp_text": PROCESS[plan["sp"]]}
                        if plan["sk"] == "1.1" else statements[plan["sp"]])
            self.plans[code] = plan
            self.catalog.append({
                "unit_code": "",
                "unit_title": plan["unit"],
                "pdp_sequence_code": code,
                "source_sequence_no": f"{number:03d}",
                "pdp_title": plan["title"],
                "sk_code": plan["sk"],
                "sk_text": standard["sk_title"],
                "sp_code": plan["sp"],
                "sp_text": standard["sp_text"],
                "textbook_ref": f"Buku Teks m/s {plan['pages']}",
            })

    def _sm2542_rows(self, year, subject):
        if (year, subject) == ("Tahun 5", "Sains"):
            return self.catalog
        return []

    @staticmethod
    def _sm2542_unique_units(rows):
        return list(dict.fromkeys((row["unit_code"], row["unit_title"]) for row in rows))

    @staticmethod
    def _commit_multi_sp(state, mapped):
        (standard,) = mapped
        state.update(standard, grouped_sp_codes=[standard["sp_code"]])

    def _plan(self, state):
        plan = self.plans[state["pdp_sequence_code"]]
        if (state["year"], state["subject"], state["unit_title"], state["sk_code"],
            state["selected_sp_codes"], state["pdp_title"]) != (
            "Tahun 5", "Sains", plan["unit"], plan["sk"], [plan["sp"]], plan["title"]
        ):
            raise ValueError("Selected PdP does not match its 2027 plan")
        return plan

    def _local_rph_text(self, state):
        plan = self._plan(state)
        return "\n".join((plan["title"], plan["objective"], plan["materials"],
                          *(" ".join(phase) for phase in plan["phases"]), plan["pbd"]))

    def _create_document(self, state, cid, renderer, suffix):
        plan = self._plan(state)
        with tempfile.NamedTemporaryFile(prefix=f"{cid}_", suffix=suffix, delete=False) as stream:
            try:
                render_rph(stream, plan, renderer, teacher=state)
            except Exception:
                Path(stream.name).unlink(missing_ok=True)
                raise
            return stream.name

    def create_word_file(self, state, _text, cid):
        return self._create_document(state, cid, _word, ".docx")

    def create_pdf_file(self, state, _text, cid):
        return self._create_document(state, cid, _pdf, ".pdf")


ROUTE = "/internal/rph/v1/sains-sk-y5-2027"


def register_downloads(app):
    from web.telegram_verified_sequence_rph_bridge import create_native_sequence_rph_blueprint

    app.register_blueprint(
        create_native_sequence_rph_blueprint(ReviewRuntime(), url_prefix=ROUTE),
        name="sains_sk_tahun5_2027",
    )
