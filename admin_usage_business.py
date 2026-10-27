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
    # Supabase is the durable source for confirmed RPH deliveries.
    try:
        deliveries = sb_request('GET', 'admin_rph_deliveries?select=telegram_user_id,subject,created_at') or []
        from collections import Counter
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        unique_rph = {str(row['telegram_user_id']) for row in deliveries}
        stats['rph_success'] = len(deliveries)
        stats['users_with_rph'] = len(unique_rph)
        stats['tracked_users'] = len(unique_rph | set()) if not stats['tracked_users'] else max(stats['tracked_users'],len(unique_rph))
        stats['active_without_rph'] = max(0,stats['tracked_users'] - stats['users_with_rph'])
        subjects = Counter(str(row['subject']) for row in deliveries if row.get('subject'))
        stats['top_subjects'] = subjects.most_common(10)
    except Exception as exc:
        print('ADMIN DURABLE RPH SUMMARY WARNING:', repr(exc), flush=True)
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
