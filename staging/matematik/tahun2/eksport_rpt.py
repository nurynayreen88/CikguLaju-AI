"""Export the SK Mathematics Year 2 RPT for DPK Edisi 3."""

import argparse
from pathlib import Path

from staging.matematik.eksport_rpt_dpk import export_table
from staging.matematik.tahun2.eksport_tahun2 import load, standards
from staging.matematik.tahun2.eksport_unit_01 import STANDARDS as UNIT_ONE_STANDARDS


def lessons_by_id(chapters):
    result = {}
    for unit, (unit_name, volume, _), plans in chapters:
        for plan in plans:
            if unit == 1:
                number = plan['lesson']
                codes = plan['sp']
                key = codes[0].rsplit('.', 1)[0]
                sk = f'{key} {UNIT_ONE_STANDARDS[key]}'
                title, dpk, textbook = plan['tajuk'], plan['dpk'], plan['bt']
                evidence = plan['evidens']
            else:
                number, codes, textbook, title, _, _, evidence = plan
                sk, dpk, _ = standards(codes)
            result[number] = (unit, unit_name, title, sk, ', '.join(codes), dpk, volume, textbook, evidence)
    return result


def export(output):
    chapters, _ = load()
    export_table(output, 2, lessons_by_id(chapters), edition='Pilihan guru',
                 review_note='42 sesi 30 minit dan 75 sesi 60 minit sepadan dengan set RPH.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    export(args.output)


if __name__ == '__main__':
    main()
