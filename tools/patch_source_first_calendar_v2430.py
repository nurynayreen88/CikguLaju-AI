#!/usr/bin/env python3
"""Apply CikguLaju v24.30 source-first routing/calendar QA hotfix to app.py.

Changes are intentionally narrow and non-destructive:
- ensure datetime.date is imported for the month calendar;
- make explicit Pilih Sendiri the only quick-PdP branch that enters manual SK/SP;
- preserve Buku Teks and RPT/SOW automatic SK/SP mapping.
"""
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
s=s.replace('from datetime import datetime, timezone, timedelta','from datetime import datetime, timezone, timedelta, date',1)
append=r'''\n\n# ===== v24.30 CUSTOM-SOURCE + CALENDAR QA HOTFIX =====\n_callback_dispatch_v2430_base = callback\n\ndef callback(cid, d):\n    ss = state.setdefault(cid, {})\n    ds = str(d or '')\n    if ds == 'qsrc92_custom' and _is_quick_pdp_v2428(ss):\n        ss['task'] = 'quick_material'\n        ss['quick_material_flow'] = True\n        ss['assessment_mode'] = 'formative'\n        ss['rph_mode'] = 'fast_custom'\n        ss.pop('selected_sk', None); ss.pop('selected_sp', None)\n        return send(cid,\n            '🎯 <b>Pilih Sendiri</b>\\n\\nPilih Topik → SK → SP. Laluan manual ini diasingkan daripada Buku Teks dan RPT/SOW.',\n            [[{'text':'➡️ Pilih Topik / SK / SP','callback_data':'quick_custom_topics'}],\n             [{'text':'⬅️ Kembali','callback_data':'qsrc91_back'}]])\n    return _callback_dispatch_v2430_base(cid, d)\n\nAPP_VERSION='v24.30-SOURCE-FIRST-CUSTOM-CALENDAR-QA'\n# ===== END v24.30 =====\n'''
if "v24.30-SOURCE-FIRST-CUSTOM-CALENDAR-QA" not in s:
    s += append
p.write_text(s,encoding='utf-8')
print('patched',p)
