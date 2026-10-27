"""Admin summary of registration, Pioneer and future subscriptions.
Read-only; no entitlement changes and no destructive migrations.
"""
from admin_usage_stats import initialize, summary
from admin_usage_telegram import format_usage_summary

def show_business_usage(cid, is_admin, db_factory, send, registered_users, sb_request):
    if not is_admin(cid):
        return send(cid, '⛔ Panel ini hanya untuk admin CikguLaju.')
    con = db_factory()
    try:
        initialize(con)
        stats = summary(con)
    finally:
        con.close()
    # Registered users come from the existing persistent directory, not event logs.
    try:
        total_users = len(registered_users())
        registered = f'<b>{total_users}</b>'
    except Exception as exc:
        print('ADMIN REGISTRATION COUNT WARNING:', repr(exc), flush=True)
        registered = '<i>Tidak dapat disemak</i>'
    # Count confirmed Pioneer entitlements only; never count pending receipts.
    try:
        from pioneer_supabase import pioneer_count
        pioneers = f'<b>{pioneer_count(sb_request)}</b>'
    except Exception as exc:
        print('ADMIN PIONEER COUNT WARNING:', repr(exc), flush=True)
        pioneers = '<i>Tidak dapat disemak</i>'
    lines = format_usage_summary(stats).split('\n')
    lines[2:2] = [
        f'👥 Jumlah pengguna berdaftar: {registered}',
        f'🏆 Pioneer aktif (disahkan): {pioneers}',
        '💳 Langganan aktif: <i>Belum tersedia — integrasi akan datang</i>',
        ''
    ]
    # Clarify the event-based count so it is not mistaken for total registration.
    message = '\n'.join(lines)
    return send(cid, message, kb=[
        [{'text':'🔄 Muat Semula','callback_data':'admin_usage_stats'}],
        [{'text':'⬅️ Kembali ke Admin','callback_data':'admin_panel'}]
    ])
