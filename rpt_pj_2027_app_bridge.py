"""CikguLaju requests-based Telegram RPT PJ 2027 callback integration.

No pyTelegramBotAPI dependency: app.py uses its own send/send_document helpers.
A caller must check server-side access on every callback.
"""
from rpt_pj_2027_delivery import STATES, YEARS, list_available, resolve_rpt, RPTDocumentUnavailable


def route(cid, data, root, *, send, send_document, allowed):
    """Return True if a callback was handled, False for unrelated callbacks."""
    if not isinstance(data, str):
        return False
    if not (data.startswith("rpt2027_pj_") or data.startswith("rpt2027_year_")):
        return False
    if not allowed(cid):
        send(cid, "🔒 RPT 2027 memerlukan akses Rakan Pembangun atau langganan aktif.")
        return True
    available = {(row["negeri"].replace(" ", "_"), row["tahun"])
                 for row in list_available(root)}
    if data.startswith("rpt2027_year_"):
        year_text = data[len("rpt2027_year_"):]
        if year_text not in {"4", "5", "6"}:
            return False
        year = int(year_text)
        if not any(y == year for _, y in available):
            return False  # preserve existing RPT placeholder
        send(cid, "📅 RPT 2027 — Tahun " + year_text,
             [[{"text": "Pendidikan Jasmani", "callback_data": "rpt2027_pj_year_" + year_text}],
              [{"text": "⬅️ Pilih Tahun", "callback_data": "rpt2027_home"}]])
        return True
    if data.startswith("rpt2027_pj_year_"):
        year_text = data[len("rpt2027_pj_year_"):]
        if year_text not in {"4", "5", "6"}:
            send(cid, "Pilihan tahun tidak sah.")
            return True
        year = int(year_text)
        rows = [[{"text": state.replace("_", " "),
                  "callback_data": f"rpt2027_pj_doc:{state}:{year}"}]
                for state in STATES if (state, year) in available]
        rows.append([{"text": "⬅️ Pilih Tahun", "callback_data": "rpt2027_home"}])
        send(cid, "Pilih negeri untuk RPT Pendidikan Jasmani Tahun " + year_text, rows)
        return True
    if data.startswith("rpt2027_pj_doc:"):
        parts = data.split(":")
        if len(parts) != 3 or parts[1] not in STATES or parts[2] not in {"4", "5", "6"}:
            send(cid, "Pilihan RPT tidak sah.")
            return True
        try:
            path = resolve_rpt(root, negeri=parts[1], tahun=int(parts[2]),
                               authorized=True)
        except RPTDocumentUnavailable:
            send(cid, "Fail RPT belum tersedia. Sila cuba kemudian.")
            return True
        send_document(cid, str(path), "RPT Pendidikan Jasmani 2027")
        return True
    return False
