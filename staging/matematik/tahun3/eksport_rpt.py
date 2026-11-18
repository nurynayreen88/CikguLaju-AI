"""Export the aligned SK Mathematics Year 3 RPT for academic review."""

import argparse
from pathlib import Path

from staging.matematik.eksport_rpt_dpk import export_table
from staging.matematik.tahun3.eksport_tahun3 import DPK_PAGES, STANDARDS, load, unit_for


def export(output):
    plans, _ = load()
    details = {}
    for number, sp, volume, textbook, title, _, _, evidence in plans:
        unit, (_, name, _) = unit_for(number)
        sk = sp.rsplit('.', 1)[0]
        details[number] = (unit, name, title, f'{sk} {STANDARDS[sk]}', sp, DPK_PAGES[sp], volume, textbook, evidence)
    export_table(output, 3, details)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    export(args.output)


if __name__ == '__main__':
    main()
