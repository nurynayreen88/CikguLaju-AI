"""Source-backed private downloads for the 2027 Year 6 SK Science sequence."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from dlp_year2_rph import _pdf, _word
from staging.sains.tahun6.eksport_2027 import build_source, render_rph


ROUTE = "/internal/rph/v1/sains-sk-y6-2027"


class ScienceYear6Runtime:
    CIKGULAJU_DB_V2600_ACTIVE = True

    def __init__(self):
        weeks, plans = build_source()
        self.plans = {}
        self.catalog = []
        for week in weeks:
            for number in week["pdp"]:
                plan = plans[number]
                code = f"SK27-SCI-Y6-PDP-{number:03d}"
                self.plans[code] = plan
                self.catalog.extend({
                    "unit_code": "", "unit_title": plan["unit"],
                    "pdp_sequence_code": code, "source_sequence_no": f"{number:03d}",
                    "pdp_title": plan["title"], "sk_code": plan["sk"], "sp_code": sp,
                    "textbook_ref": f"Buku Teks m/s {plan['pages']}",
                } for sp in plan["standards"])

    def _sm2542_rows(self, year, subject):
        return self.catalog if (year, subject) == ("Tahun 6", "Sains") else []

    @staticmethod
    def _sm2542_unique_units(rows):
        return list(dict.fromkeys((row["unit_code"], row["unit_title"]) for row in rows))

    @staticmethod
    def _commit_multi_sp(state, mapped):
        state.update(mapped[0], grouped_sp_codes=[standard["sp_code"] for standard in mapped])

    def _plan(self, state):
        plan = self.plans[state["pdp_sequence_code"]]
        if (state["year"], state["subject"], state["unit_title"], state["sk_code"],
                state["selected_sp_codes"], state["pdp_title"]) != (
                "Tahun 6", "Sains", plan["unit"], plan["sk"], plan["standards"], plan["title"]):
            raise ValueError("Invalid Year 6 Science plan selection")
        return plan

    def _local_rph_text(self, state):
        plan = self._plan(state)
        return "\n".join((plan["title"], plan["objective"], plan["materials"],
                          *(" ".join(phase) for phase in plan["phases"]), plan["pbd"]))

    def _document(self, state, cid, renderer, suffix):
        plan = self._plan(state)
        teacher = {key: state.get(f"rph_{key}") for key in ("class", "date", "time", "students")}
        teacher["reflection"] = state.get("rph_teacher_reflection")
        with NamedTemporaryFile(prefix=f"{cid}_", suffix=suffix, delete=False) as stream:
            try:
                render_rph(stream, plan, renderer, teacher=teacher)
            except Exception:
                Path(stream.name).unlink(missing_ok=True)
                raise
            return stream.name

    def create_word_file(self, state, _text, cid):
        return self._document(state, cid, _word, ".docx")

    def create_pdf_file(self, state, _text, cid):
        return self._document(state, cid, _pdf, ".pdf")


def register_downloads(app):
    from web.telegram_verified_sequence_rph_bridge import create_native_sequence_rph_blueprint

    app.register_blueprint(
        create_native_sequence_rph_blueprint(ScienceYear6Runtime(), url_prefix=ROUTE),
        name="sains_sk_tahun6_2027",
    )
