"""Extract the existing SK Mathematics standards and activity phases."""

import re

FIELD = re.compile(r'^\*\*(.+?):\*\* (.+)$', flags=re.MULTILINE)
STANDARD = re.compile(r'\b\d+\.\d+\.\d+(?=\s+—)')
TEACHER_ACTION = re.compile(r'(?<!\w)(?:Guru|guru) ')
ACTOR_BOUNDARY = re.compile(r'(?<=[.;])\s+(?=[Mm]urid |[Mm]ereka |[Gg]uru |Secara berpasangan, murid )')
PHASE_MAP = (
    ('Set induksi · 5 minit', 'Set induksi (5 minit)',
     'Paparkan rangsangan yang sesuai dan periksa pengetahuan awal.', 'Perhatikan rangsangan dan jawab soalan secara lisan.'),
    ('Aktiviti 1 · 20 minit', 'Aktiviti 1 — Penerokaan/Model (20 minit)',
     'Tunjukkan satu contoh dengan bahan yang disediakan.', 'Ikuti contoh dan jelaskan satu langkah menggunakan model.'),
    ('Aktiviti 2 · 20 minit', 'Aktiviti 2 — Aplikasi/Latihan (20 minit)',
     'Pantau latihan dan semak langkah atau hasil bersama murid.', 'Gunakan contoh berpandu untuk menyiapkan latihan.'),
)


def existing_actions(text, default_teacher, default_pupil):
    teacher, pupil = [], []
    for sentence in ACTOR_BOUNDARY.split(text):
        if TEACHER_ACTION.match(sentence):
            teacher.append(sentence[5:])
        else:
            pupil.append(sentence.removeprefix('Murid ').removeprefix('murid '))
    teacher_text = ' '.join(teacher) or default_teacher
    pupil_text = ' '.join(pupil) or default_pupil
    return teacher_text[0].upper() + teacher_text[1:], pupil_text[0].upper() + pupil_text[1:]

