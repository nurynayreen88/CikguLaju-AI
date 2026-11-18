"""Adapt the shared SK Mathematics plans to the private Telegram sequence API."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from staging.matematik.documents_2027 import YEARS, lessons_for_year, render_download


ROUTE = "/internal/rph/v1/matematik-sk-2027"


class MathSK2027Runtime:
    CIKGULAJU_DB_V2600_ACTIVE = True

    def __init__(self):
        self._plans = {}
        self._rows = {}
        for year in YEARS:
            rows = self._rows[f"Tahun {year}"] = []
            for plan in lessons_for_year(year):
                self._plans[plan.code] = plan
                rows.extend({
                    "unit_code": f"Unit {plan.unit}", "unit_title": plan.unit_title,
                    "pdp_sequence_code": plan.code, "source_sequence_no": f"{plan.number:03d}",
                    "pdp_title": plan.title, "sk_code": plan.sk, "sp_code": sp,
                    "textbook_ref": f"Buku Teks m/s {plan.pages}",
                } for sp in plan.standards)

    def _sm2542_rows(self, year, subject):
        return self._rows.get(year, []) if subject == "Matematik" else []

    @staticmethod
    def _sm2542_unique_units(rows):
        return list(dict.fromkeys((row["unit_code"], row["unit_title"]) for row in rows))

    @staticmethod
    def _commit_multi_sp(state, mapped):
        state.update(mapped[0], grouped_sp_codes=[standard["sp_code"] for standard in mapped])

    def _plan(self, state):
        plan = self._plans[state["pdp_sequence_code"]]
        if (state["subject"], state["year"], state["unit_title"], state["sk_code"],
                tuple(state["selected_sp_codes"]), state["pdp_title"]) != (
                "Matematik", f"Tahun {plan.year}", plan.unit_title, plan.sk,
                plan.standards, plan.title):
            raise ValueError("Invalid SK Mathematics plan selection")
        return plan

    def _local_rph_text(self, state):
        heading, fields, activities, reflection = self._plan(state).parts
        return "\n".join((*heading, *(" ".join(row) for row in (*fields, *activities, *reflection))))

    def _document(self, state, cid, fmt, suffix):
        teacher = {key: state.get(f"rph_{key}") for key in ("class", "date", "time", "students")}
        teacher["reflection"] = state.get("rph_teacher_reflection")
        data = render_download(self._plan(state), fmt, teacher)
        with NamedTemporaryFile(prefix=f"{cid}_", suffix=suffix, delete=False) as stream:
            try:
                stream.write(data)
            except Exception:
                Path(stream.name).unlink(missing_ok=True)
                raise
            return stream.name

    def create_word_file(self, state, _text, cid):
        return self._document(state, cid, "word", ".docx")

    def create_pdf_file(self, state, _text, cid):
        return self._document(state, cid, "pdf", ".pdf")


def register_downloads(app):
    from web.telegram_verified_sequence_rph_bridge import create_native_sequence_rph_blueprint

    app.register_blueprint(
        create_native_sequence_rph_blueprint(MathSK2027Runtime(), url_prefix=ROUTE),
        name="matematik_sk_2027",
    )
