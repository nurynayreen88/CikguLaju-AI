"""Export the SK Mathematics Year 3 RPT for DPK Edisi 3."""

import argparse
from pathlib import Path

from staging.matematik.eksport_rpt_dpk import export_table
from staging.matematik.tahun3.eksport_tahun3 import DPK_PAGES, STANDARDS, load, unit_for


def lessons_by_id(plans):
    details = {}
    for number, sp, volume, textbook, title, _, _, evidence in plans:
        unit, (_, name, _) = unit_for(number)
        sk = sp.rsplit('.', 1)[0]
        details[number] = (unit, name, title, f'{sk} {STANDARDS[sk]}', sp, DPK_PAGES[sp], volume, textbook, evidence)
    return details


def export(output):
    plans, _ = load()
    export_table(output, 3, lessons_by_id(plans), edition='Pilihan guru',
                 review_note='42 sesi 30 minit dan 75 sesi 60 minit sepadan dengan set RPH.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    export(args.output)


if __name__ == '__main__':
    main()
