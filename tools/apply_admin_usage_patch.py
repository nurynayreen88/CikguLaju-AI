"""Apply the minimal admin-menu integration to app.py locally.

Usage: python tools/apply_admin_usage_patch.py
Run on a backed-up working tree; refuses unexpected anchors and repeated patches.
Does not touch production DB or change RPH quota.
"""
from pathlib import Path

app = Path(__file__).resolve().parents[1] / 'app.py'
source = app.read_text(encoding='utf-8')
callback_anchor = "def callback(cid, d):\n    if d == 'admin_panel':"
menu_anchor = "          [{'text':'🗄️ STATUS SISTEM','callback_data':'admin_system'}],"
if "if d == 'admin_usage_stats':" in source:
    raise SystemExit('Already patched; no changes made.')
if source.count(callback_anchor) != 1 or source.count(menu_anchor) != 1:
    raise SystemExit('Expected app.py anchors not unique; no changes made.')
source = source.replace(
    callback_anchor,
    "def callback(cid, d):\n"
    "    if d == 'admin_usage_stats':\n"
    "        from admin_usage_adapter import show_admin_usage\n"
    "        return show_admin_usage(cid, _is_admin, _db, send)\n"
    "    if d == 'admin_panel':",
    1,
)
source = source.replace(
    menu_anchor,
    "          [{'text':'📊 STATISTIK PENGGUNAAN','callback_data':'admin_usage_stats'}],\n"
    + menu_anchor,
    1,
)
compile(source, str(app), 'exec')
backup = app.with_suffix('.py.before_admin_usage')
if backup.exists():
    raise SystemExit('Backup already exists; no changes made.')
backup.write_text(app.read_text(encoding='utf-8'), encoding='utf-8')
app.write_text(source, encoding='utf-8')
print('Admin usage callback/menu patched; original backed up to', backup)
