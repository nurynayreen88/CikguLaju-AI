"""Telegram-ready usage summary formatting, with explicit admin authorization.

This module does not register handlers or access the production database.
The existing bot must call it only after identifying the requesting Telegram user.
"""
from html import escape

def is_admin(user_id, admin_ids):
    """Exact string matching prevents accidental authorization by substring."""
    if user_id is None:
        return False
    return str(user_id) in {str(value).strip() for value in admin_ids if str(value).strip()}

def format_usage_summary(stats):
    """HTML-safe message for Telegram parse_mode='HTML'."""
    rows = [
        '📊 <b>CIKGULAJU AI — STATISTIK ADMIN</b>',
        '',
        f"👥 Aktif hari ini: <b>{int(stats['active_today'])}</b>",
        f"👥 Aktif 7 hari: <b>{int(stats['active_7d'])}</b>",
        f"👥 Aktif 30 hari: <b>{int(stats['active_30d'])}</b>",
        '',
        f"✅ RPH berjaya: <b>{int(stats['rph_success'])}</b>",
        '⚠️ RPH gagal: <i>Belum dijejak secara menyeluruh</i>',
        '',
        '<b>Subjek paling banyak dijana</b>',
    ]
    subjects = stats.get('top_subjects') or []
    if subjects:
        for name, count in subjects[:10]:
            rows.append(f"• {escape(str(name))}: {int(count)}")
    else:
        rows.append('Tiada rekod lagi.')
    rows.extend(['', '<i>Statistik berdasarkan peristiwa yang direkodkan sahaja.</i>'])
    return '\n'.join(rows)
