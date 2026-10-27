"""Adapter for the existing CikguLaju app.py admin panel.

Call show_admin_usage(cid, _is_admin, _db, send) from a verified callback
branch. No production handlers are modified by importing this module.
"""
from admin_usage_stats import initialize, summary
from admin_usage_telegram import format_usage_summary

def show_admin_usage(cid, is_admin, db_factory, send):
    if not is_admin(cid):
        send(cid, '⛔ Panel ini hanya untuk admin CikguLaju.')
        return False
    con = db_factory()
    try:
        initialize(con)
        message = format_usage_summary(summary(con))
    finally:
        con.close()
    send(cid, message, kb=[
        [{'text': '🔄 Muat Semula', 'callback_data': 'admin_usage_stats'}],
        [{'text': '⬅️ Kembali ke Admin', 'callback_data': 'admin_panel'}],
    ])
    return True
